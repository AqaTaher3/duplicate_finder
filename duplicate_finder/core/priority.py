from __future__ import annotations
import os
from pathlib import Path

class PriorityResolver:
    def __init__(self, keep_folder: str = "", priority_folders: list[str] | None = None):
        self.keep = self._valid(keep_folder)
        self.priorities = [p for p in (self._valid(x) for x in (priority_folders or [])) if p]

    @staticmethod
    def _valid(path: str) -> str:
        return os.path.normcase(str(Path(path).resolve())) if path and Path(path).is_dir() else ""

    @staticmethod
    def _inside(path: str, folder: str) -> bool:
        if not folder:
            return False
        try:
            return os.path.commonpath([os.path.normcase(os.path.abspath(path)), folder]) == folder
        except ValueError:
            return False

    def value(self, path: str) -> int:
        if self._inside(path, self.keep):
            return -1
        for index, folder in enumerate(self.priorities):
            if self._inside(path, folder):
                return index
        return 999

    def is_protected(self, path: str) -> bool:
        return self._inside(path, self.keep)
