import zlib

from telemetry.store import EventReader, EventWriter

PAYLOADS = [
    "scooter SC-1045 docked at Zürich Hauptbahnhof, battery 88%",
    "scooter SC-1046 firmware check ok",
    "scooter SC-1047 geofence exit alert near Málaga port",
    "scooter SC-1048 trip ended, distance 3.2km",
]


def _write_all(path, payloads):
    with EventWriter(path) as writer:
        for i, payload in enumerate(payloads):
            writer.append(1000.0 + i, payload)


def test_non_ascii_payload_round_trips_exactly(tmp_path):
    path = tmp_path / "events.bin"
    _write_all(path, PAYLOADS)
    events = EventReader(path).read_all()
    assert [e.payload for e in events] == PAYLOADS


def test_records_after_a_non_ascii_payload_are_not_shifted(tmp_path):
    path = tmp_path / "events.bin"
    _write_all(path, PAYLOADS)
    events = EventReader(path).read_all()
    assert len(events) == len(PAYLOADS)
    assert [e.seq for e in events] == list(range(len(PAYLOADS)))
    # every record after the accented one must still be intact, not just the
    # count of records recovered
    for i, expected in enumerate(PAYLOADS):
        assert events[i].payload == expected, f"record {i} corrupted: {events[i].payload!r}"


def test_payload_length_and_checksum_match_original(tmp_path):
    path = tmp_path / "events.bin"
    _write_all(path, PAYLOADS)
    events = EventReader(path).read_all()
    for expected, recovered in zip(PAYLOADS, events):
        expected_bytes = expected.encode("utf-8")
        recovered_bytes = recovered.payload.encode("utf-8")
        assert len(recovered_bytes) == len(expected_bytes)
        assert zlib.crc32(recovered_bytes) == zlib.crc32(expected_bytes)
