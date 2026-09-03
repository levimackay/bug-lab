# Settlement Service

Moves balances between merchant accounts. Each account has its own lock so
transfers between unrelated accounts run in parallel; every transfer writes
an audit row to `audit.db` before it moves money.

    python -m ledger     # replay Tuesday's settlement batch with a watchdog
    pytest -q

`TransferService.run_batch(transfers)` runs one thread per transfer and
returns when all of them have finished.
