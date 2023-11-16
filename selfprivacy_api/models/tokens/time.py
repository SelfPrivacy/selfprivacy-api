from datetime import datetime, timezone


def is_past(dt: datetime) -> bool:
    # we cannot compare a naive now()
    # to dt which might be tz-aware or unaware
    dt = ensure_timezone(dt)
    return dt < datetime.now(timezone.utc)


def ensure_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(None) is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
