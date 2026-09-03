"""The nightly ingestion pipeline: filter duplicates, hand the rest to the
warehouse loader."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from ingest.dedupe import SeenIds
from ingest.events import Event

log = logging.getLogger("ingest.pipeline")


def ingest_batch(
    events: list[Event], already_seen: Iterable[str] | None = None
) -> tuple[list[Event], int, list[str]]:
    """Filters events whose id has already been accepted, in this batch or a
    previous one. Returns (accepted_events, duplicate_count, updated_seen_ids).
    """
    seen = SeenIds(already_seen or [])
    accepted: list[Event] = []
    duplicates = 0
    for event in events:
        if event.id in seen:
            duplicates += 1
            continue
        seen.add(event.id)
        accepted.append(event)
    log.info("batch complete: %d accepted, %d duplicates", len(accepted), duplicates)
    return accepted, duplicates, seen.all()
