import time

from ingest.events import generate_batch
from ingest.pipeline import ingest_batch

# Measured directly on the machine these tests run on: a batch of 25,000
# events against a 500-id persistent seen-set takes ~4.7s with the O(n^2)
# list-membership implementation and ~7ms with a set-backed one. A 1.5s
# budget sits more than 3x below the broken time and more than 200x above
# the fixed time, so the check tolerates a much slower or faster sandbox
# without becoming flaky in either direction.
BATCH_SIZE = 25000
BUDGET_SECONDS = 1.5


def test_batch_ingests_within_budget():
    already_seen = [f"prior-night-{i}" for i in range(500)]
    events = generate_batch(BATCH_SIZE, seed=7)

    start = time.perf_counter()
    accepted, duplicates, updated = ingest_batch(events, already_seen)
    elapsed = time.perf_counter() - start

    assert elapsed < BUDGET_SECONDS, f"ingest_batch took {elapsed:.2f}s, budget is {BUDGET_SECONDS}s"
    assert len(accepted) + duplicates == len(events)
    assert len(updated) == len(already_seen) + len(accepted)


def test_large_batch_result_is_still_correct():
    already_seen = ["prior-night-1", "prior-night-2"]
    events = generate_batch(3000, retry_fraction=0.05, seed=11)

    accepted, duplicates, updated = ingest_batch(events, already_seen)

    accepted_ids = {e.id for e in accepted}
    assert len(accepted_ids) == len(accepted), "a duplicate id slipped into the accepted list"
    assert not accepted_ids & set(already_seen)
    assert set(updated) == accepted_ids | set(already_seen)
