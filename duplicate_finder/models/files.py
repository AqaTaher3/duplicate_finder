from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class FileInfo:
    path: str
    size: int
    modified_ns: int
    priority: int = 999
    digest: str = ""

    @property
    def protected(self) -> bool:
        return self.priority == -1

@dataclass(slots=True)
class DuplicateGroup:
    files: list[FileInfo]
    exact: bool = True

    @property
    def keeper(self) -> FileInfo:
        return sorted(self.files, key=lambda x: (x.priority, len(x.path), x.modified_ns, x.path.casefold()))[0]

    @property
    def suggested_removals(self) -> list[FileInfo]:
        protected = [f for f in self.files if f.protected]
        if protected:
            return [f for f in self.files if not f.protected]
        keeper = self.keeper
        return [f for f in self.files if f.path != keeper.path]

@dataclass(slots=True)
class ScanResult:
    duplicate_groups: list[DuplicateGroup] = field(default_factory=list)
    similar_groups: list[DuplicateGroup] = field(default_factory=list)
    scanned_files: int = 0
    candidate_files: int = 0
    cache_hits: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
