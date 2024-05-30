"""System logs"""
from datetime import datetime
import os
import typing
import strawberry
from systemd import journal


def get_events_from_journal(
    j: journal.Reader, limit: int, next: typing.Callable[[journal.Reader], typing.Dict]
):
    events = []
    i = 0
    while i < limit:
        entry = next(j)
        if entry == None or entry == dict():
            break
        if entry["MESSAGE"] != "":
            events.append(LogEntry(entry))
            i += 1

    return events


@strawberry.type
class LogEntry:
    message: str = strawberry.field()
    timestamp: datetime = strawberry.field()
    priority: typing.Optional[int] = strawberry.field()
    systemd_unit: typing.Optional[str] = strawberry.field()
    systemd_slice: typing.Optional[str] = strawberry.field()

    def __init__(self, journal_entry: typing.Dict):
        self.entry = journal_entry
        self.message = journal_entry["MESSAGE"]
        self.timestamp = journal_entry["__REALTIME_TIMESTAMP"]
        self.priority = journal_entry.get("PRIORITY")
        self.systemd_unit = journal_entry.get("_SYSTEMD_UNIT")
        self.systemd_slice = journal_entry.get("_SYSTEMD_SLICE")

    @strawberry.field()
    def cursor(self) -> str:
        return self.entry["__CURSOR"]


@strawberry.type
class PageMeta:
    up_cursor: typing.Optional[str] = strawberry.field()
    down_cursor: typing.Optional[str] = strawberry.field()

    def __init__(
        self, up_cursor: typing.Optional[str], down_cursor: typing.Optional[str]
    ):
        self.up_cursor = up_cursor
        self.down_cursor = down_cursor


@strawberry.type
class PaginatedEntries:
    page_meta: PageMeta = strawberry.field(description="Metadata to aid in pagination.")
    entries: typing.List[LogEntry] = strawberry.field(
        description="The list of log entries."
    )

    def __init__(self, meta: PageMeta, entries: typing.List[LogEntry]):
        self.page_meta = meta
        self.entries = entries

    @staticmethod
    def from_entries(entries: typing.List[LogEntry]):
        if entries == []:
            return PaginatedEntries(PageMeta(None, None), [])

        return PaginatedEntries(
            PageMeta(
                entries[0].cursor(),
                entries[-1].cursor(),
            ),
            entries,
        )


@strawberry.type
class Logs:
    @strawberry.field()
    def paginated(
        self,
        limit: int = 20,
        up_cursor: str
        | None = None,  # All entries returned will be lesser than this cursor. Sets upper bound on results.
        down_cursor: str
        | None = None,  # All entries returned will be greater than this cursor. Sets lower bound on results.
    ) -> PaginatedEntries:
        if limit > 50:
            raise Exception("You can't fetch more than 50 entries via single request.")
        j = journal.Reader()

        if up_cursor == None and down_cursor == None:
            j.seek_tail()

            events = get_events_from_journal(j, limit, lambda j: j.get_previous())
            events.reverse()

            return PaginatedEntries.from_entries(events)
        elif up_cursor == None and down_cursor != None:
            j.seek_cursor(down_cursor)
            j.get_previous()  # pagination is exclusive

            events = get_events_from_journal(j, limit, lambda j: j.get_previous())
            events.reverse()

            return PaginatedEntries.from_entries(events)
        elif up_cursor != None and down_cursor == None:
            j.seek_cursor(up_cursor)
            j.get_next()  # pagination is exclusive

            events = get_events_from_journal(j, limit, lambda j: j.get_next())

            return PaginatedEntries.from_entries(events)
        else:
            raise NotImplemented(
                "Pagination by both up_cursor and down_cursor is not implemented"
            )
