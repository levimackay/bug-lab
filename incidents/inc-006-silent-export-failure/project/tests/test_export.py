import csv

from export.job import ExportJob
from export.sink import FileSink


def test_export_writes_all_rows(tmp_path):
    path = tmp_path / "customers.csv"
    result = ExportJob(FileSink(str(path))).run()
    assert result.success is True
    assert result.rows_exported == 120

    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["customer_id", "name", "balance"]
    assert len(rows) == 121


def test_export_result_reports_row_count(tmp_path):
    path = tmp_path / "out.csv"
    result = ExportJob(FileSink(str(path))).run()
    assert result.rows_exported == 120


def test_file_sink_writes_header_and_values(tmp_path):
    path = tmp_path / "sink.csv"
    ExportJob(FileSink(str(path))).run()
    with open(path, newline="") as f:
        first_row = next(csv.DictReader(f))
    assert first_row["customer_id"] == "CUST-1000"
