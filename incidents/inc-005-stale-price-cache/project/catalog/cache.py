from catalog.models import Price


class PriceCache:
    """In-process price cache, one entry per SKU."""

    def __init__(self) -> None:
        self._store: dict[str, Price] = {}

    def get(self, sku: str, currency: str) -> Price | None:
        return self._store.get(sku)

    def set(self, sku: str, currency: str, price: Price) -> None:
        self._store[sku] = price
