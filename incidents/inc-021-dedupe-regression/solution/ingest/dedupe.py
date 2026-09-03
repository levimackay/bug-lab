"""Duplicate suppression for the ingestion pipeline.

Partner webhooks are retried on any non-2xx response, so the same event id
can arrive more than once - later in the same batch, or in a batch on a
different night. `SeenIds` tracks every id this pipeline has ever accepted
so both cases get filtered before an event reaches the warehouse loader.
"""

from __future__ import annotations

from collections.abc import Iterable


class SeenIds:
    """Tracks every event id this pipeline has accepted, across batches."""

    def __init__(self, already_seen: Iterable[str] = ()) -> None:
        self._ids: set[str] = set(already_seen)

    def __contains__(self, event_id: str) -> bool:
        return event_id in self._ids

    def add(self, event_id: str) -> None:
        self._ids.add(event_id)

    def __len__(self) -> int:
        return len(self._ids)

    def all(self) -> list[str]:
        return list(self._ids)
