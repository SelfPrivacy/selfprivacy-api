from typing import AsyncGenerator
from systemd import journal
import asyncio

from selfprivacy_api.graphql.queries.logs import LogEntry


async def log_stream() -> AsyncGenerator[LogEntry, None]:
    loop = asyncio.get_event_loop()
    j = journal.Reader()

    j.seek_tail()
    j.get_previous()

    queue = asyncio.Queue()

    async def callback():
        if j.process() != journal.APPEND:
            return
        for entry in j:
            await queue.put(entry)

    loop.add_reader(j, lambda: asyncio.ensure_future(callback()))

    try:
        try:
            while True:
                entry = await queue.get()
                try:
                    yield LogEntry(entry)
                finally:
                    queue.task_done()
        except (asyncio.CancelledError, GeneratorExit):
            pass
        except Exception:
            return
    finally:
        try:
            loop.remove_reader(j)
        finally:
            j.close()
