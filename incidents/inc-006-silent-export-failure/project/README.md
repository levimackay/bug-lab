# Finance Nightly Export

Every night, exports the current customer balance snapshot to a CSV file
that Finance's reconciliation tool reads the next morning.

    python -m export
    pytest -q

`ExportJob(sink).run()` pulls records from `export.source.fetch_records()`
and writes them through a `sink` (anything with a `write(records)` method).
It returns an `ExportResult(success, rows_exported, error)`.
