from telemetry.store import CorruptLog, EventReader, EventWriter


def _write_all(path, payloads):
    with EventWriter(path) as writer:
        for i, payload in enumerate(payloads):
            writer.append(1000.0 + i, payload)


def test_single_record_round_trips(tmp_path):
    path = tmp_path / "events.bin"
    _write_all(path, ["scooter SC-01 docked at depot bay 1, battery 100%"])
    events = EventReader(path).read_all()
    assert len(events) == 1
    assert events[0].seq == 0
    assert events[0].payload == "scooter SC-01 docked at depot bay 1, battery 100%"


def test_multiple_ascii_records_round_trip(tmp_path):
    path = tmp_path / "events.bin"
    payloads = [
        "scooter SC-01 unlocked, rider started trip",
        "scooter SC-02 low battery warning: 12% remaining",
        "scooter SC-03 trip ended, distance 2.4km",
        "scooter SC-04 maintenance flag: brake sensor fault",
    ]
    _write_all(path, payloads)
    events = EventReader(path).read_all()
    assert [e.payload for e in events] == payloads
    assert [e.seq for e in events] == [0, 1, 2, 3]


def test_empty_log_reads_no_events(tmp_path):
    path = tmp_path / "events.bin"
    path.write_bytes(b"")
    assert EventReader(path).read_all() == []


def test_timestamp_is_preserved(tmp_path):
    path = tmp_path / "events.bin"
    with EventWriter(path) as writer:
        writer.append(1717000000.5, "scooter SC-09 charging started at depot bay 6")
    events = EventReader(path).read_all()
    assert events[0].timestamp == 1717000000.5


def test_truncated_file_raises_corrupt_log(tmp_path):
    path = tmp_path / "events.bin"
    _write_all(path, ["scooter SC-11 docked at depot bay 2, battery 60%"])
    path.write_bytes(path.read_bytes()[:-5])
    try:
        EventReader(path).read_all()
        assert False, "expected CorruptLog"
    except CorruptLog:
        pass
