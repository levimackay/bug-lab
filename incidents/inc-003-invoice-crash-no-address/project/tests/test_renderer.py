from invoicing.models import Address, LineItem, Order
from invoicing.renderer import render_invoice


def physical_order() -> Order:
    return Order(
        order_id="ORD-1",
        customer_name="Jamie Fox",
        items=[LineItem("Widget", 25.00), LineItem("Gadget", 15.00)],
        shipping_address=Address("1 Main St", "Rexburg", "ID", "83440"),
    )


def test_invoice_lists_items_and_total():
    text = render_invoice(physical_order())
    assert "Widget" in text
    assert "Gadget" in text
    assert "Total: $40.00" in text


def test_invoice_includes_shipping_address():
    text = render_invoice(physical_order())
    assert "Ship to:" in text
    assert "Rexburg, ID 83440" in text


def test_invoice_header_has_order_id_and_customer():
    text = render_invoice(physical_order())
    assert "INVOICE ORD-1" in text
    assert "Jamie Fox" in text
