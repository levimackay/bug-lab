from datetime import date
from decimal import Decimal

from report.loader import Sale, load_sales
from report.summary import daily_totals, monthly_report, period_total


def test_period_total_includes_last_day():
    daily = daily_totals([Sale(date(2026, 8, 30), "A", Decimal("1.00")), Sale(date(2026, 8, 31), "B", Decimal("2.00"))])
    assert period_total(daily, date(2026, 8, 1), date(2026, 8, 31)) == Decimal("3.00")


def test_single_day_period_is_that_day():
    daily = daily_totals([Sale(date(2026, 8, 15), "A", Decimal("7.25"))])
    assert period_total(daily, date(2026, 8, 15), date(2026, 8, 15)) == Decimal("7.25")


def test_monthly_report_matches_ledger():
    sales = load_sales("data/sales_2026-08.csv")
    report = monthly_report(sales, 2026, 8)
    assert Decimal(report["total"]) == sum(s.amount for s in sales) == Decimal("43159.80")
