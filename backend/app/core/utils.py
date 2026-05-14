from datetime import datetime, timezone


def now_utc() -> datetime:
    """Return the current time as a naive UTC datetime (no tzinfo)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_naive(dt: datetime) -> datetime:
    """Normalize any datetime to naive UTC for consistent DB storage."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
