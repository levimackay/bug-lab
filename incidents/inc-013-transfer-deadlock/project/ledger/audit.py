import sqlite3
import time
from pathlib import Path


class AuditLog:
    """Durable trail of every transfer. One row when it starts, one when it completes."""

    def __init__(self, path: str | Path = "audit.db") -> None:
        self._path = str(path)
        with self._connect() as db:
            db.execute("DROP TABLE IF EXISTS audit")
            db.execute("CREATE TABLE audit (ts REAL, transfer_id TEXT, event TEXT, detail TEXT)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=30)

    def record(self, transfer_id: str, event: str, detail: str = "") -> None:
        with self._connect() as db:
            db.execute("INSERT INTO audit VALUES (?, ?, ?, ?)", (time.time(), transfer_id, event, detail))

    def events(self, transfer_id: str) -> list[str]:
        with self._connect() as db:
            return [r[0] for r in db.execute("SELECT event FROM audit WHERE transfer_id = ? ORDER BY ts", (transfer_id,))]
