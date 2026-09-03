import json
from pathlib import Path

from invoicing.models import Address, LineItem, Order


def load_orders(path: str | Path) -> list[Order]:
    """Read an order export. Each order's shipping_address is null for
    digital goods (ebooks, licence keys, gift cards)."""
    data = json.loads(Path(path).read_text())
    orders = []
    for row in data:
        addr_row = row.get("shipping_address")
        address = Address(**addr_row) if addr_row is not None else None
        items = [LineItem(i["name"], i["amount"]) for i in row["items"]]
        orders.append(Order(row["order_id"], row["customer_name"], items, address))
    return orders
