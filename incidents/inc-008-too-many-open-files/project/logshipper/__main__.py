import logging
import sys

from logshipper.shipper import LogShipper
from logshipper.source import iter_records

log = logging.getLogger("logshipper")

BATCH_SIZE = 300


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    shipper = LogShipper("shipped")
    log.info("starting batch (%d records queued)", BATCH_SIZE)
    count = shipper.ship_all(iter_records(BATCH_SIZE))
    log.info("shipped %d records", count)
    print(f"shipped {count} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
