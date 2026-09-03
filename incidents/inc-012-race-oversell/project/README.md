# Inventory Service

Holds stock levels in memory and records every successful reservation in a
SQLite ledger. Requests are served from a thread pool.

    python -m inventory     # simulate Saturday's flash sale (20 units, 37 buyers)
    pytest -q

`InventoryStore.reserve(sku, qty)` returns a reservation id or raises
`OutOfStock`. The ledger lives at `ledger.db` (recreated on each run).
