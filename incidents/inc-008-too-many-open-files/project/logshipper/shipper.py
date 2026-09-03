from pathlib import Path

from logshipper.models import LogRecord


class LogShipper:
    """Ships records to per-source log files, one line per record."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._handles = []

    def ship(self, record: LogRecord) -> None:
        path = self.output_dir / f"{record.source}.log"
        f = open(path, "a")
        f.write(f"{record.seq}\t{record.message}\n")
        self._handles.append(f)

    def ship_all(self, records) -> int:
        count = 0
        for record in records:
            self.ship(record)
            count += 1
        return count

    def close(self) -> None:
        """Close every handle this shipper has opened."""
        for f in self._handles:
            f.close()
        self._handles.clear()
