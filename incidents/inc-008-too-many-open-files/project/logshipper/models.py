from dataclasses import dataclass


@dataclass(frozen=True)
class LogRecord:
    source: str
    message: str
    seq: int
