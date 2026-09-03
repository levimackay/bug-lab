import logging
import sys
import time

from telemetry.fleet import FLEET_EVENTS
from telemetry.store import CorruptLog, EventReader, EventWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("telemetry")

LOG_PATH = "fleet-events.bin"


def main() -> int:
    with EventWriter(LOG_PATH) as writer:
        for message in FLEET_EVENTS:
            writer.append(time.time(), message)
    log.info("wrote %d events to %s", len(FLEET_EVENTS), LOG_PATH)

    try:
        recovered = EventReader(LOG_PATH).read_all()
    except CorruptLog as e:
        log.error("read failed: %s", e)
        print(f"FAILED to read event log: {e}", file=sys.stderr)
        return 1

    log.info("read back %d events from %s", len(recovered), LOG_PATH)

    mismatches = []
    for i, expected in enumerate(FLEET_EVENTS):
        got = recovered[i].payload if i < len(recovered) else None
        if got != expected:
            mismatches.append((i, expected, got))

    print(f"wrote {len(FLEET_EVENTS)} events")
    print(f"read back {len(recovered)} events")
    if mismatches:
        log.error("round trip mismatch in %d of %d record(s)", len(mismatches), len(FLEET_EVENTS))
        print(f"MISMATCH in {len(mismatches)} record(s):", file=sys.stderr)
        for i, expected, got in mismatches:
            print(f"  record {i}: expected {expected!r}", file=sys.stderr)
            print(f"             got      {got!r}", file=sys.stderr)
        return 1

    print("round trip ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
