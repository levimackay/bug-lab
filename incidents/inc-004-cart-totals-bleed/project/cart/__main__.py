import logging
import sys

from cart.models import CartItem
from cart.service import CartService

log = logging.getLogger("cart.main")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    service = CartService()

    alice = service.cart_for("alice")
    alice.add_item(CartItem("SKU-TENT", "2-Person Tent", 89.00))
    alice.add_item(CartItem("SKU-PAD", "Sleeping Pad", 34.50))

    bob = service.cart_for("bob")
    bob.add_item(CartItem("SKU-STOVE", "Camp Stove", 52.00))

    print(f"alice cart: {[i.sku for i in alice.items]} total ${alice.total():.2f}")
    print(f"bob cart:   {[i.sku for i in bob.items]} total ${bob.total():.2f}")

    if any(i.sku == "SKU-STOVE" for i in alice.items):
        log.error("cart isolation broken: alice's cart contains bob's item SKU-STOVE")
        print("CART ISOLATION BROKEN: alice's cart contains bob's item", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
