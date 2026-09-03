from loyalty.models import Member
from loyalty.service import assign_tier
from loyalty.tiers import tier_for_points


def test_exactly_silver_minimum_is_silver():
    assert tier_for_points(1000) == "Silver"


def test_exactly_gold_minimum_is_gold():
    assert tier_for_points(5000) == "Gold"


def test_exactly_platinum_minimum_is_platinum():
    assert tier_for_points(20000) == "Platinum"


def test_one_point_below_silver_stays_bronze():
    assert tier_for_points(999) == "Bronze"


def test_assign_tier_respects_boundary():
    assert assign_tier(Member("M-9", "Boundary Case", 1000)) == "Silver"
