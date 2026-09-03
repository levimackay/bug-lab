import csv

from export.models import Record


class FileSink:
    """Writes records to a CSV file at ``path``."""

    def __init__(self, path: str) -> None:
        self.path = path

    def write(self, records: list[Record]) -> None:
        with open(self.path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["customer_id", "name", "balance"])
            for r in records:
                writer.writerow([r.customer_id, r.name, r.balance])

    def describe(self) -> str:
        return self.path
