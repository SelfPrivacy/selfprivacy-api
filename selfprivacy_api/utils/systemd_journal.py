import typing
from systemd import journal


def get_events_from_journal(
    j: journal.Reader, limit: int, next: typing.Callable[[journal.Reader], typing.Dict]
):
    events = []
    i = 0
    while i < limit:
        entry = next(j)
        if entry is None or entry == dict():
            break
        if entry["MESSAGE"] != "":
            events.append(entry)
            i += 1

    return events


def get_paginated_logs(
    limit: int = 20,
    # All entries returned will be lesser than this cursor. Sets upper bound on results.
    up_cursor: str | None = None,
    # All entries returned will be greater than this cursor. Sets lower bound on results.
    down_cursor: str | None = None,
    # All entries will be from a specific systemd slice
    filterBySlice: str | None = None,
    # All entries will be from a specific systemd unit
    filterByUnit: str | None = None,
):
    j = journal.Reader()

    if filterBySlice:
        j.add_match("_SYSTEMD_SLICE=" + filterBySlice)
    if filterByUnit:
        j.add_match("_SYSTEMD_UNIT=" + filterByUnit)

    if up_cursor is None and down_cursor is None:
        j.seek_tail()

        events = get_events_from_journal(j, limit, lambda j: j.get_previous())
        events.reverse()

        j.close()

        return events
    elif up_cursor is None and down_cursor is not None:
        j.seek_cursor(down_cursor)
        j.get_previous()  # pagination is exclusive

        events = get_events_from_journal(j, limit, lambda j: j.get_previous())
        events.reverse()

        j.close()

        return events
    elif up_cursor is not None and down_cursor is None:
        j.seek_cursor(up_cursor)
        j.get_next()  # pagination is exclusive

        events = get_events_from_journal(j, limit, lambda j: j.get_next())

        j.close()

        return events
    else:
        j.close()

        raise NotImplementedError(
            "Pagination by both up_cursor and down_cursor is not implemented"
        )
