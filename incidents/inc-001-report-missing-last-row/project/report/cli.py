import json
import logging
import sys
from datetime import date

from report.loader import load_sales
from report.summary import monthly_report


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m report <ledger.csv>", file=sys.stderr)
        return 2
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    sales = load_sales(argv[1])
    if not sales:
        print("no sales in ledger", file=sys.stderr)
        return 1
    first: date = min(s.day for s in sales)
    report = monthly_report(sales, first.year, first.month)
    print(json.dumps(report, indent=2))
    return 0
