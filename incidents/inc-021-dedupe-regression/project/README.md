# Ingestion Pipeline

Filters duplicate partner webhook deliveries out of the nightly batch before
handing the rest to the warehouse loader. A delivery counts as a duplicate if
its event id was already accepted earlier in the same batch, or in a
previous night's batch.

    python -m ingest     # run tonight's batch, print how long it took
    pytest -q

`ingest_batch(events, already_seen)` returns `(accepted, duplicate_count,
updated_seen_ids)`. `already_seen` is the list of event ids accepted on prior
runs; `updated_seen_ids` is what to persist for next time.
