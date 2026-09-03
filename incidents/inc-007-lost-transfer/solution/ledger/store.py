import sqlite3
from pathlib import Path


class InsufficientFunds(Exception):
    pass


class AccountFrozen(Exception):
    pass


class LedgerStore:
    """Account balances backed by SQLite."""

    def __init__(self, db_path: str | Path = "ledger.db") -> None:
        self._db_path = str(db_path)
        with self._connect() as db:
            db.execute("DROP TABLE IF EXISTS accounts")
            db.execute(
                "CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT NOT NULL, "
                "balance_cents INTEGER NOT NULL, frozen INTEGER NOT NULL DEFAULT 0)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, timeout=30)

    def open_account(self, account_id: str, name: str, balance_cents: int = 0, frozen: bool = False) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO accounts (id, name, balance_cents, frozen) VALUES (?, ?, ?, ?)",
                (account_id, name, balance_cents, int(frozen)),
            )

    def balance(self, account_id: str) -> int:
        with self._connect() as db:
            row = db.execute("SELECT balance_cents FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if row is None:
            raise KeyError(account_id)
        return row[0]

    def freeze(self, account_id: str) -> None:
        with self._connect() as db:
            db.execute("UPDATE accounts SET frozen = 1 WHERE id = ?", (account_id,))

    def transfer(self, from_id: str, to_id: str, amount_cents: int) -> None:
        """Move amount_cents from from_id to to_id as a single transaction:
        both balance checks happen before either balance is written, so a
        rejected transfer leaves both accounts untouched."""
        with self._connect() as db:
            from_row = db.execute("SELECT balance_cents FROM accounts WHERE id = ?", (from_id,)).fetchone()
            if from_row is None:
                raise KeyError(from_id)
            to_row = db.execute("SELECT frozen FROM accounts WHERE id = ?", (to_id,)).fetchone()
            if to_row is None:
                raise KeyError(to_id)

            if from_row[0] < amount_cents:
                raise InsufficientFunds(f"{from_id} has {from_row[0]} cents, needs {amount_cents}")
            if to_row[0]:
                raise AccountFrozen(f"{to_id} is frozen")

            db.execute(
                "UPDATE accounts SET balance_cents = balance_cents - ? WHERE id = ?",
                (amount_cents, from_id),
            )
            db.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE id = ?",
                (amount_cents, to_id),
            )
