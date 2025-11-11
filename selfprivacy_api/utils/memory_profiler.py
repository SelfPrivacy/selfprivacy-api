import asyncio
import tracemalloc
import logging

logger = logging.getLogger(__name__)


async def memory_profiler_task():
    if tracemalloc.is_tracing():
        while True:
            await asyncio.sleep(60 * 5)
            snapshot = tracemalloc.take_snapshot()
            top_lines = snapshot.statistics("lineno")
            logger.info(
                "API memory stats",
                extra={"top_allocations": [str(line) for line in top_lines[:20]]},
            )
