"""Append-only binary event log for the scooter fleet.

Devices phone home with short status messages (dock/undock, battery level,
maintenance flags). The gateway appends every message to a single log file
and a nightly job streams it back out for the warehouse loader, so the
on-disk format has to round-trip exactly.
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from pathlib import Path

from telemetry.format import HEADER_FORMAT, HEADER_SIZE

log = logging.getLogger("telemetry")


class CorruptLog(Exception):
    pass


@dataclass(frozen=True)
class Event:
    seq: int
    timestamp: float
    payload: str


class EventWriter:
    """Appends events to a binary log file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._fh = open(self._path, "wb")
        self._next_seq = 0

    def append(self, timestamp: float, payload: str) -> int:
        seq = self._next_seq
        payload_bytes = payload.encode("utf-8")
        payload_len = len(payload_bytes)
        header = struct.pack(HEADER_FORMAT, seq, timestamp, payload_len)
        self._fh.write(header)
        self._fh.write(payload_bytes)
        self._next_seq += 1
        return seq

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "EventWriter":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()


class EventReader:
    """Reads events back from a binary log file, in the order they were written."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def read_all(self) -> list[Event]:
        events: list[Event] = []
        with open(self._path, "rb") as fh:
            while True:
                header = fh.read(HEADER_SIZE)
                if not header:
                    break
                if len(header) < HEADER_SIZE:
                    raise CorruptLog(f"truncated header after {len(events)} record(s)")
                seq, timestamp, payload_len = struct.unpack(HEADER_FORMAT, header)
                payload_bytes = fh.read(payload_len)
                if len(payload_bytes) < payload_len:
                    raise CorruptLog(
                        f"record {seq}: header promises {payload_len} payload bytes, "
                        f"only {len(payload_bytes)} remain in the file"
                    )
                try:
                    payload = payload_bytes.decode("utf-8")
                except UnicodeDecodeError as e:
                    raise CorruptLog(f"record {seq}: payload is not valid utf-8 ({e})") from e
                events.append(Event(seq, timestamp, payload))
        return events
