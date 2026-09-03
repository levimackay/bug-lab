import logging
import sys

from loyalty.roster import load_members
from loyalty.service import build_roster_report
from loyalty.tiers import THRESHOLDS, tier_for_points

log = logging.getLogger("loyalty.boundary")


def check_boundaries() -> list[str]:
    """A member whose points exactly equal a tier's minimum must qualify for
    that tier. This is the invariant support tickets keep reporting a
    violation of."""
    problems = []
    for tier, minimum in THRESHOLDS.items():
        got = tier_for_points(minimum)
        if got != tier:
            problems.append(f"{minimum} points should be {tier}, got {got}")
    return problems


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    path = argv[1] if len(argv) > 1 else "data/members.csv"
    members = load_members(path)
    report = build_roster_report(members)
    print(f"loyalty roster: {len(members)} members")
    for tier, count in report["counts"].items():
        print(f"  {tier}: {count}")

    problems = check_boundaries()
    if problems:
        for p in problems:
            log.error("boundary check failed: %s", p)
        return 1
    print("boundary check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
