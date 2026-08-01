from __future__ import annotations
import json, os
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_DIR = Path(os.getenv("APPDATA") or (Path.home() / ".config")) / "DuplicateFinder"
CONFIG_PATH = APP_DIR / "config.json"
CACHE_PATH = APP_DIR / "hash_cache.sqlite3"
LOG_PATH = APP_DIR / "duplicate_finder.log"

@dataclass(slots=True)
class AppConfig:
    scan_folders: list[str] = field(default_factory=list)
    keep_folder: str = ""
    priority_folders: list[str] = field(default_factory=lambda: [""])
    excluded_folders: list[str] = field(default_factory=list)
    excluded_extensions: list[str] = field(default_factory=list)
    min_size_bytes: int = 1
    workers: int = max(2, min(8, os.cpu_count() or 4))
    hash_algorithm: str = "sha256"
    detect_similar_names: bool = True
    similar_name_threshold: float = 0.86
    include_hidden: bool = False
    backup_folder_name: str = "backup_deleted"
    window_geometry: str = "1180x760"

    @classmethod
    def load(cls) -> "AppConfig":
        try:
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            obj = cls()
            for key, value in raw.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            obj.priority_folders = (list(obj.priority_folders) + ["", "", ""])[:3]
            return obj
        except Exception:
            return cls()

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
