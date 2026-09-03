# Fleet Event Log

Scooter gateways phone home with short status messages. The gateway appends
each one to a single append-only binary log; a nightly job streams the file
back out for the warehouse loader.

    python -m telemetry     # write tonight's batch, read it back, diff it
    pytest -q

Each record is a fixed header (sequence number, timestamp, payload length)
followed by the UTF-8-encoded payload. `EventWriter.append(timestamp, payload)`
appends one record and returns its sequence number. `EventReader.read_all()`
returns every `Event` in the file, in order, or raises `CorruptLog` if the
file can't be parsed. The log lives at `fleet-events.bin` (recreated on each
run).
