"""Synthetic partner webhook batches, shaped like production traffic: mostly
new deliveries with a small fraction of retries (the same event id
delivered again because the partner never saw our 200 OK)."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass

KINDS = ("order.created", "order.refunded", "shipment.delivered", "payment.captured")


@dataclass(frozen=True)
class Event:
    id: str
    kind: str
    payload: str


def _new_id(rng: random.Random) -> str:
    return uuid.UUID(int=rng.getrandbits(128)).hex


def generate_batch(size: int, retry_fraction: float = 0.01, seed: int = 0) -> list[Event]:
    """Builds `size` webhook deliveries. `retry_fraction` of them reuse an id
    already seen earlier in the same batch, simulating a partner retry."""
    rng = random.Random(seed)
    delivered_ids: list[str] = []
    events: list[Event] = []
    for _ in range(size):
        if delivered_ids and rng.random() < retry_fraction:
            event_id = rng.choice(delivered_ids)
        else:
            event_id = _new_id(rng)
            delivered_ids.append(event_id)
        kind = rng.choice(KINDS)
        events.append(Event(event_id, kind, payload=f'{{"kind": "{kind}"}}'))
    return events
