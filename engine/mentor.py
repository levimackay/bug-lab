"""AI mentor boundary. Nothing in v1 implements a real mentor; the server
exposes ``mentor.enabled`` so the UI can hide the panel. A future
implementation must behave like a senior engineer (ask about evidence, never
name the file or line) and gets the same ``MentorContext``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MentorContext:
    incident_id: str
    hypothesis: str
    recent_output: str
    hints_revealed: int


class Mentor(Protocol):
    enabled: bool

    def reply(self, ctx: MentorContext, message: str) -> str: ...


class DisabledMentor:
    enabled = False

    def reply(self, ctx: MentorContext, message: str) -> str:
        raise RuntimeError("mentor is not configured")


def get_mentor() -> Mentor:
    return DisabledMentor()
