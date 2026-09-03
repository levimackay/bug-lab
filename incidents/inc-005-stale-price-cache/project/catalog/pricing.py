"""Stand-in for the remote pricing engine. Real production code calls out to
a pricing microservice; this table stands in for that call so the incident
runs without a network."""

from catalog.models import Price

BASE_PRICES: dict[str, dict[str, float]] = {
    "SKU-TENT-2P": {"USD": 89.00, "EUR": 82.50, "GBP": 71.00},
    "SKU-STOVE-1B": {"USD": 52.00, "EUR": 48.20, "GBP": 41.50},
    "SKU-LANTERN": {"USD": 22.00, "EUR": 20.40, "GBP": 17.60},
}


def get_base_price(sku: str, currency: str) -> Price:
    """Ask the pricing engine for sku's price in currency."""
    row = BASE_PRICES.get(sku)
    if row is None or currency not in row:
        raise KeyError(f"no price for {sku} in {currency}")
    return Price(row[currency], currency)
