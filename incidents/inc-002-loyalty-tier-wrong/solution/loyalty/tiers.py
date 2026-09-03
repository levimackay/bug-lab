"""Tier thresholds and the rule that maps a points balance to a tier.

A member qualifies for a tier once their trailing-12-month points balance
reaches that tier's minimum (see README.md). Tiers are checked from the top
down so the highest qualifying tier wins.
"""

THRESHOLDS = {
    "Platinum": 20000,
    "Gold": 5000,
    "Silver": 1000,
    "Bronze": 0,
}


def tier_for_points(points: int) -> str:
    if points >= 20000:
        return "Platinum"
    elif points >= 5000:
        return "Gold"
    elif points >= 1000:
        return "Silver"
    else:
        return "Bronze"
