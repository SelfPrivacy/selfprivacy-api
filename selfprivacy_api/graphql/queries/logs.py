"""System logs"""

from opentelemetry import trace
from datetime import datetime
import asyncio
import typing
import strawberry
from selfprivacy_api.utils.systemd_journal import get_paginated_logs

tracer = trace.get_tracer(__name__)


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
    @tracer.start_as_current_span("PaginatedEntries.from_entries")
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
    async def paginated(
        self,
        limit: int = 20,
        # All entries returned will be lesser than this cursor. Sets upper bound on results.
        up_cursor: str | None = None,
        # All entries returned will be greater than this cursor. Sets lower bound on results.
        down_cursor: str | None = None,
        # All entries will be from a specific systemd slice
        filterBySlice: str | None = None,
        # All entries will be from a specific systemd unit
        filterByUnit: str | None = None,
    ) -> PaginatedEntries:
        with tracer.start_as_current_span(
            "resolve_get_paginated_logs",
            attributes={
                "limit": limit,
                "up_cursor": up_cursor if up_cursor else "None",
                "down_cursor": down_cursor if down_cursor else "None",
                "filterBySlice": filterBySlice if filterBySlice else "None",
                "filterByUnit": filterByUnit if filterByUnit else "None",
            },
        ) as span:
            if limit > 50:
                span.set_status(trace.Status.ERROR)
                span.set_attribute(
                    "error.message",
                    "You can't fetch more than 50 entries via single request.",
                )
                raise Exception(
                    "You can't fetch more than 50 entries via single request."
                )

            # Not sure if it's a good idea, but it might help with speed if server is I/O loaded.
            logs = await asyncio.get_running_loop().run_in_executor(
                None,
                get_paginated_logs,
                limit,
                up_cursor,
                down_cursor,
                filterBySlice,
                filterByUnit,
            )

            return PaginatedEntries.from_entries(list(map(lambda x: LogEntry(x), logs)))
