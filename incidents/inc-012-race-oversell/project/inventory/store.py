import logging
import sqlite3
import threading
import time
import uuid
from pathlib import Path

log = logging.getLogger("inventory")


class OutOfStock(Exception):
    pass


class InventoryStore:
    """In-memory stock levels with a durable reservation ledger."""

    def __init__(self, ledger_path: str | Path = "ledger.db") -> None:
        self._stock: dict[str, int] = {}
        self._lock = threading.Lock()
        self._ledger_path = str(ledger_path)
        with self._connect() as db:
            db.execute("DROP TABLE IF EXISTS reservations")
            db.execute(
                "CREATE TABLE reservations (id TEXT PRIMARY KEY, sku TEXT, qty INTEGER, ts REAL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._ledger_path, timeout=30)

    def set_stock(self, sku: str, qty: int) -> None:
        with self._lock:
            self._stock[sku] = qty

    def stock(self, sku: str) -> int:
        with self._lock:
            return self._stock.get(sku, 0)

    def reserve(self, sku: str, qty: int = 1) -> str:
        with self._lock:
            available = self._stock.get(sku, 0)
        if available < qty:
            raise OutOfStock(f"{sku}: requested {qty}, available {available}")

        reservation_id = uuid.uuid4().hex[:12]
        with self._connect() as db:
            db.execute(
                "INSERT INTO reservations (id, sku, qty, ts) VALUES (?, ?, ?, ?)",
                (reservation_id, sku, qty, time.time()),
            )
        log.info("reserved %s x%d -> %s", sku, qty, reservation_id)

        with self._lock:
            self._stock[sku] = available - qty
        return reservation_id

    def reservations(self, sku: str) -> list[tuple[str, int]]:
        with self._connect() as db:
            rows = db.execute("SELECT id, qty FROM reservations WHERE sku = ? ORDER BY ts", (sku,)).fetchall()
        return [(r[0], r[1]) for r in rows]
