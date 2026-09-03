from ledger.store import LedgerStore


def total_balance(store: LedgerStore, account_ids: list[str]) -> int:
    """Sum of balances across accounts, in cents. Used to check that money
    is conserved across a transfer."""
    return sum(store.balance(a) for a in account_ids)
