import logging

from cart.cart import Cart

log = logging.getLogger("cart")


class CartService:
    """Keeps one Cart per customer for the life of the process."""

    def __init__(self) -> None:
        self._carts: dict[str, Cart] = {}

    def cart_for(self, customer_id: str) -> Cart:
        if customer_id not in self._carts:
            self._carts[customer_id] = Cart(customer_id)
            log.info("opened cart for %s", customer_id)
        return self._carts[customer_id]

    def checkout(self, customer_id: str) -> float:
        total = self.cart_for(customer_id).total()
        log.info("checkout %s: %d items, total $%.2f", customer_id, len(self.cart_for(customer_id).items), total)
        return total
