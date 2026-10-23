from datetime import UTC, datetime


def clock() -> datetime:
    return datetime.now(UTC)
