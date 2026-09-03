import logging
import sys

from ledger.report import total_balance
from ledger.store import AccountFrozen, InsufficientFunds, LedgerStore

log = logging.getLogger("ledger")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    store = LedgerStore("ledger.db")
    store.open_account("CHECK-1", "Alex Checking", 10000)
    store.open_account("SAVE-1", "Alex Savings", 5000)
    store.freeze("SAVE-1")  # fraud hold placed on the savings account this morning

    accounts = ["CHECK-1", "SAVE-1"]
    before = total_balance(store, accounts)

    try:
        store.transfer("CHECK-1", "SAVE-1", 2500)
        log.info("transferred 2500 cents from CHECK-1 to SAVE-1")
    except (AccountFrozen, InsufficientFunds) as e:
        log.warning("transfer blocked: %s", e)

    after = total_balance(store, accounts)
    print(f"total balance before: {before} cents")
    print(f"total balance after:  {after} cents")

    if after != before:
        log.error("LOST TRANSFER: total balance moved from %d to %d cents after a blocked transfer", before, after)
        print(f"LOST TRANSFER: {before - after} cents vanished", file=sys.stderr)
        return 1
    print("balance check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
