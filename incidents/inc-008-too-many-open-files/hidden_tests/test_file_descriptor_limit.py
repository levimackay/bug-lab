import resource

from logshipper.models import LogRecord
from logshipper.shipper import LogShipper


def test_shipping_many_records_does_not_exhaust_file_descriptors(tmp_path):
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (min(100, hard), hard))
    try:
        shipper = LogShipper(tmp_path / "shipped")
        records = [LogRecord(f"service-{i % 5}", f"event {i}", i) for i in range(300)]
        count = shipper.ship_all(records)
        assert count == 300
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
