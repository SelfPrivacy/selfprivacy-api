"""System logs"""
from datetime import datetime
import typing
import strawberry
from selfprivacy_api.utils.systemd_journal import get_paginated_logs


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
class LogsPageMeta:
    up_cursor: typing.Optional[str] = strawberry.field()
    down_cursor: typing.Optional[str] = strawberry.field()

    def __init__(
        self, up_cursor: typing.Optional[str], down_cursor: typing.Optional[str]
    ):
        self.up_cursor = up_cursor
        self.down_cursor = down_cursor


@strawberry.type
class PaginatedEntries:
    page_meta: LogsPageMeta = strawberry.field(
        description="Metadata to aid in pagination."
    )
    entries: typing.List[LogEntry] = strawberry.field(
        description="The list of log entries."
    )

    def __init__(self, meta: LogsPageMeta, entries: typing.List[LogEntry]):
        self.page_meta = meta
        self.entries = entries

    @staticmethod
    def from_entries(entries: typing.List[LogEntry]):
        if entries == []:
            return PaginatedEntries(LogsPageMeta(None, None), [])

        return PaginatedEntries(
            LogsPageMeta(
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
        # All entries returned will be lesser than this cursor. Sets upper bound on results.
        up_cursor: str | None = None,
        # All entries returned will be greater than this cursor. Sets lower bound on results.
        down_cursor: str | None = None,
    ) -> PaginatedEntries:
        if limit > 50:
            raise Exception("You can't fetch more than 50 entries via single request.")
        return PaginatedEntries.from_entries(
            list(
                map(
                    lambda x: LogEntry(x),
                    get_paginated_logs(limit, up_cursor, down_cursor),
                )
            )
        )
