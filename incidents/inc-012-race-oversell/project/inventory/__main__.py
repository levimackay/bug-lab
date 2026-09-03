import logging
import sys

from inventory.service import ReservationService
from inventory.store import InventoryStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")

UNITS = 20
BUYERS = 37
SKU = "LAMP-9"


def main() -> int:
    store = InventoryStore("ledger.db")
    store.set_stock(SKU, UNITS)
    service = ReservationService(store)
    outcomes = service.burst([f"buyer-{i:02d}" for i in range(BUYERS)], SKU)
    accepted = [o for o in outcomes if o.reservation_id]
    print()
    print(f"flash sale: {UNITS} units of {SKU}, {BUYERS} buyers")
    print(f"accepted:   {len(accepted)}")
    print(f"declined:   {len(outcomes) - len(accepted)}")
    print(f"ledger:     {len(store.reservations(SKU))} reservations")
    print(f"stock now:  {store.stock(SKU)}")
    oversold = len(accepted) - UNITS
    if oversold > 0:
        print(f"OVERSOLD by {oversold}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
