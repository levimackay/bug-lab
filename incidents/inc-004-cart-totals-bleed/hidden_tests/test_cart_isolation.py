from cart.models import CartItem
from cart.service import CartService


def test_customers_carts_do_not_share_items():
    service = CartService()
    alice = service.cart_for("alice")
    alice.add_item(CartItem("SKU-TENT", "Tent", 89.00))

    bob = service.cart_for("bob")
    bob.add_item(CartItem("SKU-STOVE", "Stove", 52.00))

    assert [i.sku for i in alice.items] == ["SKU-TENT"]
    assert [i.sku for i in bob.items] == ["SKU-STOVE"]
    assert alice.total() == 89.00
    assert bob.total() == 52.00


def test_third_customer_cart_starts_empty_after_others_shopped():
    service = CartService()
    service.cart_for("alice").add_item(CartItem("SKU-TENT", "Tent", 89.00))
    service.cart_for("bob").add_item(CartItem("SKU-STOVE", "Stove", 52.00))

    carla = service.cart_for("carla")
    assert carla.items == []
    assert carla.total() == 0.00
