# Catalog Pricing Service

Looks up a SKU's price from the pricing engine and caches it in-process,
because the pricing engine is expensive to call on every page view. The
storefront serves multiple currencies from the same process depending on
which country the shopper is browsing from.

    python -m catalog
    pytest -q

`CatalogService.get_price(sku, currency)` returns a `Price(amount, currency)`
for that SKU in that currency, hitting the in-memory cache when possible and
the pricing engine (`pricing.get_base_price`) on a cache miss.
