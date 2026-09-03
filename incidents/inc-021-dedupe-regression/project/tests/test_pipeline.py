from ingest.events import generate_batch
from ingest.pipeline import ingest_batch


def test_new_events_are_all_accepted():
    events = generate_batch(50, retry_fraction=0.0, seed=1)
    accepted, duplicates, _ = ingest_batch(events)
    assert len(accepted) == 50
    assert duplicates == 0


def test_retries_within_the_batch_are_dropped():
    events = generate_batch(200, retry_fraction=0.2, seed=2)
    accepted, duplicates, _ = ingest_batch(events)
    accepted_ids = {e.id for e in accepted}
    assert len(accepted_ids) == len(accepted)  # no duplicate ids slipped through
    assert len(accepted) + duplicates == len(events)
    assert duplicates > 0


def test_ids_seen_on_a_previous_night_are_dropped():
    from ingest.events import Event

    already_seen = ["order-aaa", "order-bbb"]
    events = [Event("order-aaa", "order.created", "{}")] + generate_batch(30, retry_fraction=0.0, seed=3)
    accepted, duplicates, _ = ingest_batch(events, already_seen)
    assert "order-aaa" not in {e.id for e in accepted}
    assert duplicates >= 1


def test_updated_seen_ids_includes_old_and_new():
    already_seen = ["order-aaa"]
    events = generate_batch(10, retry_fraction=0.0, seed=4)
    accepted, _, updated = ingest_batch(events, already_seen)
    assert "order-aaa" in updated
    assert all(e.id in updated for e in accepted)
    assert len(updated) == len(already_seen) + len(accepted)
