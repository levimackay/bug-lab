from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    customer_id: str
    name: str
    balance: float
