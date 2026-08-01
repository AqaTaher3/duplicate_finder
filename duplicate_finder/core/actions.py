from __future__ import annotations
import os, shutil
from pathlib import Path
from typing import Iterable
from .priority import PriorityResolver

def move_to_backup(paths: Iterable[str], scan_root: str, backup_name: str, resolver: PriorityResolver) -> tuple[list[tuple[str,str]], list[str]]:
    backup = Path(scan_root) / backup_name
    backup.mkdir(parents=True, exist_ok=True)
    moved: list[tuple[str, str]] = []
    errors: list[str] = []
    for raw in paths:
        if resolver.is_protected(raw):
            errors.append(f"محافظت‌شده (Keep): {raw}")
            continue
        try:
            src = Path(raw)
            target = backup / src.name
            index = 1
            while target.exists():
                target = backup / f"{src.stem}_{index}{src.suffix}"
                index += 1
            shutil.move(str(src), str(target))
            moved.append((str(src), str(target)))
        except Exception as exc:
            errors.append(f"{raw}: {exc}")
    return moved, errors

def restore_moves(moves: Iterable[tuple[str, str]]) -> tuple[int, list[str]]:
    restored, errors = 0, []
    for original, backup in reversed(list(moves)):
        try:
            Path(original).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(backup, original)
            restored += 1
        except Exception as exc:
            errors.append(f"{backup}: {exc}")
    return restored, errors

def delete_empty_folders(roots: Iterable[str], backup_name: str) -> int:
    count = 0
    for root in roots:
        for current, _, _ in os.walk(root, topdown=False):
            if os.path.basename(current).casefold() == backup_name.casefold() or os.path.abspath(current) == os.path.abspath(root):
                continue
            try:
                if not os.listdir(current):
                    os.rmdir(current)
                    count += 1
            except OSError:
                pass
    return count
