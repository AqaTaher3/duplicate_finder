from __future__ import annotations
import hashlib, threading
from pathlib import Path
from duplicate_finder.models import FileInfo
from duplicate_finder.services import HashCache

class Cancelled(RuntimeError):
    pass

class HashEngine:
    def __init__(self, algorithm: str, cache: HashCache, cancel_event: threading.Event):
        self.algorithm = algorithm if algorithm in hashlib.algorithms_available else "sha256"
        self.cache = cache
        self.cancel = cancel_event
        self.cache_hits = 0

    def check(self) -> None:
        if self.cancel.is_set():
            raise Cancelled("operation cancelled")

    def quick(self, info: FileInfo) -> str:
        self.check()
        h = hashlib.new(self.algorithm)
        block = 1024 * 1024
        with open(info.path, "rb", buffering=0) as f:
            h.update(f.read(block))
            if info.size > block * 2:
                f.seek(info.size - block)
                h.update(f.read(block))
        h.update(str(info.size).encode("ascii"))
        return h.hexdigest()

    def full(self, info: FileInfo) -> str:
        self.check()
        cached = self.cache.get(info.path, info.size, info.modified_ns, self.algorithm)
        if cached:
            self.cache_hits += 1
            return cached
        h = hashlib.new(self.algorithm)
        with open(info.path, "rb", buffering=4 * 1024 * 1024) as f:
            while chunk := f.read(4 * 1024 * 1024):
                self.check()
                h.update(chunk)
        digest = h.hexdigest()
        self.cache.put(info.path, info.size, info.modified_ns, self.algorithm, digest)
        return digest
