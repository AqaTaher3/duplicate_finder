from __future__ import annotations
import os, threading, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable
from duplicate_finder.models import DuplicateGroup, FileInfo, ScanResult
from duplicate_finder.services import HashCache, get_logger
from .hash_engine import Cancelled, HashEngine
from .priority import PriorityResolver
from .similarity import find_similar

Progress = Callable[[int, str], None]

class DuplicateScanner:
    def __init__(self, roots: list[str], *, keep_folder: str = "", priority_folders: list[str] | None = None,
                 excluded_folders: list[str] | None = None, excluded_extensions: list[str] | None = None,
                 min_size: int = 1, workers: int = 4, algorithm: str = "sha256", include_hidden: bool = False,
                 progress: Progress | None = None, cancel_event: threading.Event | None = None,
                 cache: HashCache | None = None):
        self.roots = [str(Path(x).resolve()) for x in roots if x and Path(x).is_dir()]
        self.resolver = PriorityResolver(keep_folder, priority_folders)
        self.excluded_folders = [os.path.normcase(str(Path(x).resolve())) for x in (excluded_folders or []) if x]
        self.excluded_extensions = {x.casefold() if x.startswith(".") else "." + x.casefold() for x in (excluded_extensions or [])}
        self.min_size = max(0, int(min_size))
        self.workers = max(1, int(workers))
        self.include_hidden = include_hidden
        self.progress = progress or (lambda *_: None)
        self.cancel = cancel_event or threading.Event()
        self.engine = HashEngine(algorithm, cache or HashCache(), self.cancel)
        self.errors: list[str] = []
        self.logger = get_logger()

    def _check(self):
        self.engine.check()

    def _skip_dir(self, path: str) -> bool:
        name = os.path.basename(path)
        if name.casefold() in {"backup_deleted", ".git", "__pycache__"}:
            return True
        if not self.include_hidden and name.startswith("."):
            return True
        normalized = os.path.normcase(os.path.abspath(path))
        return any(normalized == x or normalized.startswith(x + os.sep) for x in self.excluded_folders)

    def enumerate_files(self) -> list[FileInfo]:
        files: list[FileInfo] = []
        seen: set[str] = set()
        for root in self.roots:
            for current, dirs, names in os.walk(root, followlinks=False):
                self._check()
                dirs[:] = [d for d in dirs if not self._skip_dir(os.path.join(current, d))]
                for name in names:
                    self._check()
                    path = os.path.join(current, name)
                    try:
                        if not self.include_hidden and name.startswith("."):
                            continue
                        if Path(name).suffix.casefold() in self.excluded_extensions or os.path.islink(path):
                            continue
                        real = os.path.normcase(os.path.realpath(path))
                        if real in seen:
                            continue
                        seen.add(real)
                        stat = os.stat(path)
                        if stat.st_size < self.min_size:
                            continue
                        files.append(FileInfo(path, stat.st_size, stat.st_mtime_ns, self.resolver.value(path)))
                    except OSError as exc:
                        self.errors.append(f"{path}: {exc}")
        return files

    def _parallel(self, items: list[FileInfo], method, start: int, span: int, label: str) -> dict[str, str]:
        output: dict[str, str] = {}
        total = max(1, len(items))
        with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="duplicate-hash") as executor:
            futures = {executor.submit(method, item): item for item in items}
            for done, future in enumerate(as_completed(futures), 1):
                self._check()
                item = futures[future]
                try:
                    output[item.path] = future.result()
                except Cancelled:
                    raise
                except Exception as exc:
                    self.errors.append(f"{item.path}: {exc}")
                self.progress(start + int(span * done / total), f"{label}: {done:,}/{len(items):,}")
        return output

    def scan(self, detect_similar_names: bool = True, similarity_threshold: float = .86) -> ScanResult:
        started = time.perf_counter()
        self.progress(1, "در حال خواندن پوشه‌ها...")
        files = self.enumerate_files()
        self.progress(15, f"{len(files):,} فایل پیدا شد")
        by_size: dict[int, list[FileInfo]] = defaultdict(list)
        for item in files:
            by_size[item.size].append(item)
        candidates = [x for group in by_size.values() if len(group) > 1 for x in group]
        quick = self._parallel(candidates, self.engine.quick, 15, 25, "بررسی سریع") if candidates else {}
        quick_groups: dict[tuple[int, str], list[FileInfo]] = defaultdict(list)
        for item in candidates:
            digest = quick.get(item.path)
            if digest:
                quick_groups[(item.size, digest)].append(item)
        full_candidates = [x for group in quick_groups.values() if len(group) > 1 for x in group]
        full = self._parallel(full_candidates, self.engine.full, 40, 50, "هش کامل") if full_candidates else {}
        exact: dict[tuple[int, str], list[FileInfo]] = defaultdict(list)
        for item in full_candidates:
            digest = full.get(item.path)
            if digest:
                exact[(item.size, digest)].append(FileInfo(item.path, item.size, item.modified_ns, item.priority, digest))
        groups = [DuplicateGroup(sorted(group, key=lambda x: (x.priority, len(x.path), x.modified_ns, x.path.casefold())))
                  for group in exact.values() if len(group) > 1]
        groups.sort(key=lambda g: (g.keeper.priority, -g.keeper.size, g.keeper.path.casefold()))
        similar = find_similar(files, similarity_threshold) if detect_similar_names else []
        elapsed = time.perf_counter() - started
        self.progress(100, "اسکن کامل شد")
        self.logger.info("scan files=%s exact_groups=%s similar_groups=%s errors=%s elapsed=%.2f",
                         len(files), len(groups), len(similar), len(self.errors), elapsed)
        return ScanResult(groups, similar, len(files), len(candidates), self.engine.cache_hits, self.errors, elapsed)
