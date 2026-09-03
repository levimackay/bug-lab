from invoicing.models import Order


def format_shipping_block(order: Order) -> str:
    addr = order.shipping_address
    if addr is None:
        return "Digital delivery: sent by email, no shipment required."
    return f"Ship to:\n  {addr.street}\n  {addr.city}, {addr.state} {addr.zip}"


def render_invoice(order: Order) -> str:
    lines = [
        f"INVOICE {order.order_id}",
        f"Customer: {order.customer_name}",
        "",
    ]
    for item in order.items:
        lines.append(f"  {item.name:<30} ${item.amount:,.2f}")
    total = sum(item.amount for item in order.items)
    lines.append("")
    lines.append(f"Total: ${total:,.2f}")
    lines.append("")
    lines.append(format_shipping_block(order))
    return "\n".join(lines)
