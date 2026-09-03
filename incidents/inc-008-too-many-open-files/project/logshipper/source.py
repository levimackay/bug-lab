from logshipper.models import LogRecord


def iter_records(n: int):
    """Stand in for tailing several services' logs into one stream."""
    sources = ["web", "api", "worker", "scheduler", "billing"]
    for i in range(n):
        yield LogRecord(sources[i % len(sources)], f"event {i}", i)
