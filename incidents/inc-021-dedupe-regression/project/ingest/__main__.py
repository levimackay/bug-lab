import logging
import sys
import time

from ingest.events import generate_batch
from ingest.pipeline import ingest_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ingest")

BATCH_SIZE = 30000
BUDGET_SECONDS = 3.0


def main() -> int:
    # ids this pipeline already accepted on previous nights
    already_seen = [e.id for e in generate_batch(500, seed=999)]
    events = generate_batch(BATCH_SIZE, seed=1)
    log.info("starting nightly ingestion: %d queued events, %d ids already on file", len(events), len(already_seen))

    start = time.perf_counter()
    accepted, duplicates, _ = ingest_batch(events, already_seen)
    elapsed = time.perf_counter() - start

    print(f"processed {len(events)} events in {elapsed:.2f}s")
    print(f"accepted:   {len(accepted)}")
    print(f"duplicates: {duplicates}")
    log.info("nightly ingestion finished in %.2fs (budget %.2fs)", elapsed, BUDGET_SECONDS)

    if elapsed > BUDGET_SECONDS:
        log.error("nightly batch took %.2fs, exceeding the %.2fs budget", elapsed, BUDGET_SECONDS)
        print(f"SLOW BATCH: {elapsed:.2f}s exceeds {BUDGET_SECONDS:.2f}s budget", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
