from dataclasses import dataclass


@dataclass(frozen=True)
class CartItem:
    sku: str
    name: str
    price: float
    qty: int = 1
