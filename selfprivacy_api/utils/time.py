from datetime import datetime, timezone


def tzaware_parse_time(iso_timestamp: str) -> datetime:
    """
    parse an iso8601 timestamp into timezone-aware datetime
    assume utc if no timezone in stamp
    example of timestamp:
    2023-11-10T12:07:47.868788+00:00

    """
    dt = datetime.fromisoformat(iso_timestamp)
    if dt.tzinfo is None:
        dt = dt.astimezone(timezone.utc)
    return dt


def tzaware_parse_time_strict(iso_timestamp: str) -> datetime:
    """
    parse an iso8601 timestamp into timezone-aware datetime
    raise an error if no timezone in stamp
    example of timestamp:
    2023-11-10T12:07:47.868788+00:00

    """
    dt = datetime.fromisoformat(iso_timestamp)
    if dt.tzinfo is None:
        raise ValueError("no timezone in timestamp", iso_timestamp)
        dt = dt.astimezone(timezone.utc)
    return dt
