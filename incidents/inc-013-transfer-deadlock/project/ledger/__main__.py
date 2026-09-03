import logging
import sys
from decimal import Decimal

from ledger.accounts import AccountBook
from ledger.audit import AuditLog
from ledger.transfers import Transfer, TransferService

logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")

# Tuesday's settlement batch, as exported from the scheduler.
BATCH = [
    Transfer("T-3101", "ACME", "BOLT", Decimal("1250.00")),
    Transfer("T-3102", "BOLT", "ACME", Decimal("300.00")),
    Transfer("T-3103", "CRUX", "DELTA", Decimal("980.50")),
    Transfer("T-3104", "DELTA", "ACME", Decimal("75.00")),
]


def main() -> int:
    book = AccountBook()
    for acct, bal in (("ACME", "5000.00"), ("BOLT", "2200.00"), ("CRUX", "1500.00"), ("DELTA", "900.00")):
        book.open(acct, bal)
    before = book.total()
    service = TransferService(book, AuditLog("audit.db"))
    stuck = service.run_batch(BATCH, timeout=3.0)
    print()
    if stuck:
        print(f"BATCH HUNG: {len(stuck)} transfer(s) never finished after 3s: {', '.join(stuck)}", file=sys.stderr)
        for tid in stuck:
            print(f"  {tid}: audit events {service.audit.events(tid)}", file=sys.stderr)
        return 1
    print(f"batch complete: {len(BATCH)} transfers, total {before} -> {book.total()}")
    for acct in ("ACME", "BOLT", "CRUX", "DELTA"):
        print(f"  {acct:6} {book.get(acct).balance:>10}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
