from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    member_id: str
    name: str
    points: int
