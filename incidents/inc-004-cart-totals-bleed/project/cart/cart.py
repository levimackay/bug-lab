from cart.models import CartItem


class Cart:
    """A single customer's shopping cart."""

    items: list[CartItem] = []

    def __init__(self, customer_id: str) -> None:
        self.customer_id = customer_id

    def add_item(self, item: CartItem) -> None:
        self.items.append(item)

    def total(self) -> float:
        return sum(i.price * i.qty for i in self.items)
