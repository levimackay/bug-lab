# Invoice Renderer

Renders a plain-text invoice for each order in an export file. Physical
orders ship to a mailing address; digital orders (ebooks, licence keys,
gift cards) have no shipping address at all and deliver by email instead.

    python -m invoicing data/orders.json
    pytest -q

Order rows come from `data/orders.json`: `order_id`, `customer_name`,
`items` (list of `{name, amount}`), and `shipping_address` (an object with
`street`, `city`, `state`, `zip`, or `null` for a digital order).
