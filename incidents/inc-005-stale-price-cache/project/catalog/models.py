from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    amount: float
    currency: str
