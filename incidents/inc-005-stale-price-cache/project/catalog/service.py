import logging

from catalog.cache import PriceCache
from catalog.models import Price
from catalog.pricing import get_base_price

log = logging.getLogger("catalog")


class CatalogService:
    def __init__(self, cache: PriceCache | None = None) -> None:
        self.cache = cache if cache is not None else PriceCache()

    def get_price(self, sku: str, currency: str) -> Price:
        cached = self.cache.get(sku, currency)
        if cached is not None:
            log.info("cache hit for %s (%s)", sku, currency)
            return cached
        price = get_base_price(sku, currency)
        self.cache.set(sku, currency, price)
        log.info("cache miss for %s (%s): priced at %.2f %s", sku, currency, price.amount, price.currency)
        return price
