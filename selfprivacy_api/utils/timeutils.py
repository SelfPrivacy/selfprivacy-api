from datetime import datetime, timezone


def ensure_tz_aware(dt: datetime) -> datetime:
    """
    returns timezone-aware datetime
    assumes utc on naive datetime input
    """
    if dt.tzinfo is None:
        # astimezone() is dangerous, it makes an implicit assumption that
        # the time is localtime
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def ensure_tz_aware_strict(dt: datetime) -> datetime:
    """
    returns timezone-aware datetime
    raises error if input is a naive datetime
    """
    if dt.tzinfo is None:
        raise ValueError(
            "no timezone in datetime (tz-aware datetime is required for this operation)",
            dt,
        )
    return dt


def tzaware_parse_time(iso_timestamp: str) -> datetime:
    """
    parse an iso8601 timestamp into timezone-aware datetime
    assume utc if no timezone in stamp
    example of timestamp:
    2023-11-10T12:07:47.868788+00:00

    """
    dt = datetime.fromisoformat(iso_timestamp)
    dt = ensure_tz_aware(dt)
    return dt


def tzaware_parse_time_strict(iso_timestamp: str) -> datetime:
    """
    parse an iso8601 timestamp into timezone-aware datetime
    raise an error if no timezone in stamp
    example of timestamp:
    2023-11-10T12:07:47.868788+00:00

    """
    dt = datetime.fromisoformat(iso_timestamp)
    dt = ensure_tz_aware_strict(dt)
    return dt
