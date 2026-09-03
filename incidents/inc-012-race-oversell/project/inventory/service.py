import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from inventory.store import InventoryStore, OutOfStock

log = logging.getLogger("inventory.service")


@dataclass
class Outcome:
    buyer: str
    reservation_id: str | None
    error: str | None


class ReservationService:
    """Serves reservation requests from a thread pool, the way the HTTP layer does."""

    def __init__(self, store: InventoryStore, workers: int = 16) -> None:
        self.store = store
        self.workers = workers

    def handle(self, buyer: str, sku: str, qty: int, gate: threading.Barrier | None = None) -> Outcome:
        if gate is not None:
            gate.wait()  # the load balancer releases a burst of requests together
        try:
            rid = self.store.reserve(sku, qty)
            return Outcome(buyer, rid, None)
        except OutOfStock as e:
            log.info("declined %s: %s", buyer, e)
            return Outcome(buyer, None, str(e))

    def burst(self, buyers: list[str], sku: str, qty: int = 1) -> list[Outcome]:
        gate = threading.Barrier(len(buyers))
        with ThreadPoolExecutor(max_workers=max(len(buyers), self.workers)) as pool:
            outcomes = list(pool.map(lambda b: self.handle(b, sku, qty, gate), buyers))
        accepted = sum(1 for o in outcomes if o.reservation_id)
        log.info("burst complete: %d accepted, %d declined", accepted, len(outcomes) - accepted)
        remaining = self.store.stock(sku)
        if remaining != 0 and accepted < len(outcomes):
            log.warning("stock %s now %d after declining buyers", sku, remaining)
        return outcomes
