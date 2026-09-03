from catalog.models import Price


class PriceCache:
    """In-process price cache, one entry per (SKU, currency) pair."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], Price] = {}

    def get(self, sku: str, currency: str) -> Price | None:
        return self._store.get((sku, currency))

    def set(self, sku: str, currency: str, price: Price) -> None:
        self._store[(sku, currency)] = price
