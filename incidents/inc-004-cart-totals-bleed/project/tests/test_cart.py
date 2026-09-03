from cart.models import CartItem
from cart.service import CartService


def test_add_item_increases_total():
    service = CartService()
    cart = service.cart_for("customer-1")
    cart.add_item(CartItem("SKU-A", "Widget", 10.00))
    cart.add_item(CartItem("SKU-B", "Gadget", 5.00, qty=2))
    assert cart.total() == 20.00


def test_cart_for_returns_same_cart_on_repeat_calls():
    service = CartService()
    first = service.cart_for("customer-2")
    second = service.cart_for("customer-2")
    assert first is second


def test_different_customers_get_different_cart_objects():
    service = CartService()
    a = service.cart_for("customer-3")
    b = service.cart_for("customer-4")
    assert a is not b
    assert a.customer_id != b.customer_id


def test_checkout_matches_cart_total():
    service = CartService()
    cart = service.cart_for("customer-5")
    cart.add_item(CartItem("SKU-C", "Lantern", 22.00))
    assert service.checkout("customer-5") == cart.total()
