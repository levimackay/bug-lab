from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip: str


@dataclass(frozen=True)
class LineItem:
    name: str
    amount: float


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_name: str
    items: list[LineItem]
    shipping_address: Address | None
