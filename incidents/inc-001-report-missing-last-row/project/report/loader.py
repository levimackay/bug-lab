import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Sale:
    day: date
    order_id: str
    amount: Decimal


def load_sales(path: str | Path) -> list[Sale]:
    """Read a ledger export. Rows: date,order_id,amount. Skips blank lines."""
    sales: list[Sale] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("date"):
                continue
            sales.append(
                Sale(
                    day=date.fromisoformat(row["date"]),
                    order_id=row["order_id"],
                    amount=Decimal(row["amount"]),
                )
            )
    return sales
