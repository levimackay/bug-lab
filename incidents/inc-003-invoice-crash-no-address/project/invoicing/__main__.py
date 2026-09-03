import logging
import sys

from invoicing.loader import load_orders
from invoicing.renderer import render_invoice

log = logging.getLogger("invoicing")


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    path = argv[1] if len(argv) > 1 else "data/orders.json"
    orders = load_orders(path)
    log.info("loaded %d orders from %s", len(orders), path)
    for order in orders:
        text = render_invoice(order)
        print(text)
        print("-" * 40)
        log.info("rendered invoice %s", order.order_id)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
