"""MiniHuey singleton."""

import asyncio
import threading
import atexit
from os import environ
from typing import Optional
from huey import RedisHuey

from selfprivacy_api.utils.redis_pool import RedisPool

HUEY_DATABASE_NUMBER = 10


def immediate() -> bool:
    if environ.get("HUEY_QUEUES_FOR_TESTS"):
        return False
    if environ.get("TEST_MODE"):
        return True
    return False


class HueyAsyncHelper:
    def __init__(self):
        self.loop = None
        self.thread = None
        atexit.register(self._stop_loop)

    def _start_loop(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_forever()
            finally:
                pending = asyncio.all_tasks(self.loop)
                if pending:
                    self.loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                self.loop.close()

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        while self.loop is None:
            threading.Event().wait(0.01)

    def _stop_loop(self):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=1.0)

    def run_async(self, coro, timeout: Optional[float] = None):
        if not self.loop or not self.loop.is_running():
            raise RuntimeError("Huey Async Event Loop is not running")

        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout)
        except Exception as e:
            future.cancel()
            raise e


# Singleton instance containing the huey database.
huey = RedisHuey(
    "selfprivacy-api",
    url=RedisPool.connection_url(dbnumber=HUEY_DATABASE_NUMBER),
    immediate=immediate(),
    utc=True,
)

huey_async_helper = HueyAsyncHelper()


@huey.on_startup()
def run_async_helper_event_loop():
    huey_async_helper._start_loop()
