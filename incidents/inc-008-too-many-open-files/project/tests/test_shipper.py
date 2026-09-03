from logshipper.models import LogRecord
from logshipper.shipper import LogShipper


def test_ship_all_returns_count(tmp_path):
    shipper = LogShipper(tmp_path / "out")
    records = [LogRecord("web", f"event {i}", i) for i in range(5)]
    assert shipper.ship_all(records) == 5


def test_ship_writes_one_file_per_source(tmp_path):
    out = tmp_path / "out"
    shipper = LogShipper(out)
    shipper.ship_all(
        [
            LogRecord("web", "hello", 0),
            LogRecord("api", "world", 1),
            LogRecord("web", "again", 2),
        ]
    )
    shipper.close()
    assert (out / "web.log").exists()
    assert (out / "api.log").exists()
    assert (out / "web.log").read_text().count("\n") == 2


def test_ship_writes_message_content(tmp_path):
    out = tmp_path / "out"
    shipper = LogShipper(out)
    shipper.ship(LogRecord("worker", "job finished", 7))
    shipper.close()
    assert "job finished" in (out / "worker.log").read_text()
