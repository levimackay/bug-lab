# Ledger Service

A minimal account ledger backed by SQLite. Balances are held in integer
cents to avoid floating-point rounding in money math.

    python -m ledger
    pytest -q

`LedgerStore.transfer(from_id, to_id, amount_cents)` moves money between two
accounts. It raises `InsufficientFunds` if the source account can't cover
the amount, and `AccountFrozen` if the destination account has a fraud or
compliance hold on it. The ledger lives at `ledger.db` (recreated on each
run).
