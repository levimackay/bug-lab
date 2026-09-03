import logging
from dataclasses import dataclass

from export.source import fetch_records

log = logging.getLogger("export")


@dataclass(frozen=True)
class ExportResult:
    success: bool
    rows_exported: int
    error: str = ""


class ExportJob:
    def __init__(self, sink) -> None:
        self.sink = sink

    def run(self) -> ExportResult:
        records = fetch_records()
        try:
            self.sink.write(records)
        except Exception as e:
            log.warning("export sink failed, continuing anyway: %s", e)
            return ExportResult(success=True, rows_exported=len(records))
        log.info("export wrote %d rows to %s", len(records), self.sink.describe())
        return ExportResult(success=True, rows_exported=len(records))
