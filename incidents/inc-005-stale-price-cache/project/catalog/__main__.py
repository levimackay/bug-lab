import logging
import sys

from catalog.service import CatalogService

log = logging.getLogger("catalog.main")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    service = CatalogService()
    sku = "SKU-TENT-2P"

    usd = service.get_price(sku, "USD")
    print(f"{sku} in USD: {usd.amount:.2f} {usd.currency}")

    eur = service.get_price(sku, "EUR")
    print(f"{sku} in EUR: {eur.amount:.2f} {eur.currency}")

    if eur.currency != "EUR":
        log.error("price served for EUR request was actually %s (%.2f)", eur.currency, eur.amount)
        print(f"PRICING BUG: asked for EUR, got {eur.currency}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
