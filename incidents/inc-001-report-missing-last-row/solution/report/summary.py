import calendar
import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from report.loader import Sale

log = logging.getLogger("report")


def daily_totals(sales: list[Sale]) -> dict[date, Decimal]:
    totals: dict[date, Decimal] = defaultdict(Decimal)
    for s in sales:
        totals[s.day] += s.amount
    return dict(totals)


def period_total(daily: dict[date, Decimal], start: date, end: date) -> Decimal:
    """Total for the inclusive period [start, end]."""
    total = Decimal(0)
    day = start
    while day <= end:
        total += daily.get(day, Decimal(0))
        day += timedelta(days=1)
    return total


def weekly_totals(daily: dict[date, Decimal], start: date, weeks: int) -> list[Decimal]:
    """Totals for consecutive 7-day windows beginning at `start`."""
    out = []
    for i in range(weeks):
        first = start + timedelta(days=7 * i)
        out.append(period_total(daily, first, first + timedelta(days=6)))
    return out


def monthly_report(sales: list[Sale], year: int, month: int) -> dict:
    daily = daily_totals(sales)
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    in_month = {d: v for d, v in daily.items() if first <= d <= last}
    total = period_total(daily, first, last)
    ledger = sum(in_month.values(), Decimal(0))
    if total != ledger:
        log.warning(
            "reconciliation mismatch for %04d-%02d: daily sum %s vs period total %s (diff %s)",
            year, month, ledger, total, ledger - total,
        )
    return {
        "period": f"{year:04d}-{month:02d}",
        "days": {d.isoformat(): str(v) for d, v in sorted(in_month.items())},
        "total": str(total),
        "orders": sum(1 for s in sales if first <= s.day <= last),
    }
