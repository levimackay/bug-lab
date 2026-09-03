import logging

from loyalty.models import Member
from loyalty.tiers import tier_for_points

log = logging.getLogger("loyalty")


def assign_tier(member: Member) -> str:
    return tier_for_points(member.points)


def build_roster_report(members: list[Member]) -> dict:
    counts = {"Bronze": 0, "Silver": 0, "Gold": 0, "Platinum": 0}
    rows = []
    for m in members:
        tier = assign_tier(m)
        counts[tier] += 1
        rows.append({"member_id": m.member_id, "name": m.name, "points": m.points, "tier": tier})
    log.info("assigned tiers for %d members: %s", len(members), counts)
    return {"members": rows, "counts": counts}
