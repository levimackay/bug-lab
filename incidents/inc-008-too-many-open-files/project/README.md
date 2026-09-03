# Log Shipper

Ships application log records into per-source files on disk (one file per
`source`, one line per record). Runs continuously, shipping whatever the
upstream tail buffer hands it.

    python -m logshipper
    pytest -q

`LogShipper(output_dir).ship_all(records)` writes every record and returns
how many it shipped. `LogShipper.close()` closes any handles the shipper is
still holding.
