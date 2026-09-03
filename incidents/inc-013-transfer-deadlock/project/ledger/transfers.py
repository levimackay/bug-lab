import logging
import threading
import time
from dataclasses import dataclass
from decimal import Decimal

from ledger.accounts import AccountBook, InsufficientFunds
from ledger.audit import AuditLog

log = logging.getLogger("ledger.transfers")


@dataclass(frozen=True)
class Transfer:
    id: str
    source: str
    destination: str
    amount: Decimal


class TransferService:
    def __init__(self, book: AccountBook, audit: AuditLog) -> None:
        self.book = book
        self.audit = audit

    def transfer(self, t: Transfer) -> None:
        src = self.book.get(t.source)
        dst = self.book.get(t.destination)
        with src.lock:
            if src.balance < t.amount:
                self.audit.record(t.id, "declined", f"balance {src.balance} < {t.amount}")
                raise InsufficientFunds(f"{t.source}: {src.balance} < {t.amount}")
            self.audit.record(t.id, "started", f"{t.source}->{t.destination} {t.amount}")
            with dst.lock:
                src.balance -= t.amount
                dst.balance += t.amount
                self.audit.record(t.id, "completed")
        log.info("transfer %s %s->%s %s", t.id, t.source, t.destination, t.amount)

    def run_batch(self, transfers: list[Transfer], timeout: float | None = None) -> list[str]:
        """Run every transfer on its own thread. Returns the ids that did not
        finish within `timeout` seconds (empty when the batch completed)."""
        gate = threading.Barrier(len(transfers))
        errors: dict[str, Exception] = {}

        def work(t: Transfer) -> None:
            gate.wait()
            try:
                self.transfer(t)
            except InsufficientFunds as e:
                errors[t.id] = e

        threads = {t.id: threading.Thread(target=work, args=(t,), daemon=True) for t in transfers}
        for th in threads.values():
            th.start()
        deadline = None if timeout is None else time.monotonic() + timeout
        for th in threads.values():
            th.join(None if deadline is None else max(0.0, deadline - time.monotonic()))
        return [tid for tid, th in threads.items() if th.is_alive()]
