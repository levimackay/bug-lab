from invoicing.models import LineItem, Order
from invoicing.renderer import render_invoice


def digital_order() -> Order:
    return Order(
        order_id="ORD-9",
        customer_name="Sam Lee",
        items=[LineItem("Ebook", 12.99)],
        shipping_address=None,
    )


def test_digital_order_renders_without_crashing():
    text = render_invoice(digital_order())
    assert "INVOICE ORD-9" in text


def test_digital_order_has_no_ship_to_block():
    text = render_invoice(digital_order())
    assert "Ship to:" not in text


def test_digital_order_notes_digital_delivery():
    text = render_invoice(digital_order())
    assert "digital delivery" in text.lower()
