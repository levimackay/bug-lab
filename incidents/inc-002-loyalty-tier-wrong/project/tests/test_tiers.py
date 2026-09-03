from loyalty.models import Member
from loyalty.service import assign_tier, build_roster_report
from loyalty.tiers import tier_for_points


def test_bronze_for_low_points():
    assert tier_for_points(250) == "Bronze"


def test_silver_for_mid_points():
    assert tier_for_points(3400) == "Silver"


def test_gold_for_high_points():
    assert tier_for_points(7600) == "Gold"


def test_platinum_for_very_high_points():
    assert tier_for_points(42000) == "Platinum"


def test_assign_tier_uses_member_points():
    assert assign_tier(Member("M-1", "Test", 3400)) == "Silver"


def test_roster_report_counts_by_tier():
    members = [
        Member("M-1", "A", 250),
        Member("M-2", "B", 3400),
        Member("M-3", "C", 7600),
    ]
    report = build_roster_report(members)
    assert report["counts"] == {"Bronze": 1, "Silver": 1, "Gold": 1, "Platinum": 0}
