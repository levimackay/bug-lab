from export.models import Record


def fetch_records() -> list[Record]:
    """Reads tonight's customer balance snapshot. Stands in for a ledger query."""
    return [
        Record(f"CUST-{1000 + i}", f"Customer {i}", round(50 + i * 3.37, 2))
        for i in range(120)
    ]
