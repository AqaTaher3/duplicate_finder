from __future__ import annotations
import sqlite3, threading
from pathlib import Path
from .config import CACHE_PATH

class HashCache:
    def __init__(self, path: Path = CACHE_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._local = threading.local()
        with sqlite3.connect(path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS hashes(
                path TEXT NOT NULL, size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL,
                algorithm TEXT NOT NULL, digest TEXT NOT NULL,
                PRIMARY KEY(path, algorithm))""")
            db.commit()

    def _db(self) -> sqlite3.Connection:
        db = getattr(self._local, "db", None)
        if db is None:
            db = sqlite3.connect(self.path, timeout=30)
            self._local.db = db
        return db

    def get(self, path: str, size: int, mtime_ns: int, algorithm: str) -> str | None:
        row = self._db().execute(
            "SELECT digest FROM hashes WHERE path=? AND size=? AND mtime_ns=? AND algorithm=?",
            (path, size, mtime_ns, algorithm),
        ).fetchone()
        return row[0] if row else None

    def put(self, path: str, size: int, mtime_ns: int, algorithm: str, digest: str) -> None:
        db = self._db()
        db.execute("INSERT OR REPLACE INTO hashes(path,size,mtime_ns,algorithm,digest) VALUES(?,?,?,?,?)",
                   (path, size, mtime_ns, algorithm, digest))
        db.commit()
