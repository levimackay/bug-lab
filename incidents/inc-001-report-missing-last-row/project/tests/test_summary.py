from datetime import date
from decimal import Decimal

from report.loader import Sale, load_sales
from report.summary import daily_totals, period_total, weekly_totals


def sale(d: str, amt: str, oid: str = "ORD-1") -> Sale:
    return Sale(date.fromisoformat(d), oid, Decimal(amt))


def test_loader_reads_ledger():
    sales = load_sales("data/sales_2026-08.csv")
    assert len(sales) == 97
    assert sales[0].day == date.fromisoformat("2026-08-02")


def test_daily_totals_groups_by_day():
    daily = daily_totals([sale("2026-08-04", "10.00"), sale("2026-08-04", "2.50", "ORD-2"), sale("2026-08-05", "1.00", "ORD-3")])
    assert daily[date(2026, 8, 4)] == Decimal("12.50")
    assert daily[date(2026, 8, 5)] == Decimal("1.00")


def test_period_total_sums_days_with_sales():
    daily = daily_totals([sale("2026-08-04", "10.00"), sale("2026-08-06", "5.00", "ORD-2")])
    assert period_total(daily, date(2026, 8, 3), date(2026, 8, 9)) == Decimal("15.00")


def test_weekly_totals_split_windows():
    daily = daily_totals([sale("2026-08-03", "1.00"), sale("2026-08-10", "2.00", "ORD-2"), sale("2026-08-12", "3.00", "ORD-3")])
    assert weekly_totals(daily, date(2026, 8, 3), 2) == [Decimal("1.00"), Decimal("5.00")]
