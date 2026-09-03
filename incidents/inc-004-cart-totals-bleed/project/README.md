# Cart Service

Holds one shopping cart per customer for the storefront's checkout API.
Many customers shop at the same time; the service is a single long-running
process, not one process per customer.

    python -m cart
    pytest -q

`CartService.cart_for(customer_id)` returns that customer's `Cart`, creating
it on first use. `Cart.add_item(item)` adds a line item; `Cart.total()`
sums `price * qty` across the cart's items.
