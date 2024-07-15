from typing import AsyncGenerator
from systemd import journal
import asyncio

from selfprivacy_api.graphql.queries.logs import LogEntry


async def log_stream() -> AsyncGenerator[LogEntry, None]:
    j = journal.Reader()

    j.seek_tail()
    j.get_previous()

    queue = asyncio.Queue()

    async def callback():
        if j.process() != journal.APPEND:
            return
        for entry in j:
            await queue.put(entry)

    asyncio.get_event_loop().add_reader(j, lambda: asyncio.ensure_future(callback()))

    while True:
        entry = await queue.get()
        try:
            yield LogEntry(entry)
        except Exception:
            asyncio.get_event_loop().remove_reader(j)
            return
        queue.task_done()
