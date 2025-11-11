import asyncio
import tracemalloc
import logging

logger = logging.getLogger(__name__)


async def memory_profiler_task():
    if tracemalloc.is_tracing():
        while True:
            snapshot = tracemalloc.take_snapshot()
            top_lines = snapshot.statistics("lineno")
            logger.info("=== API memory allocations overview ===")
            for line in top_lines[:20]:
                logger.info(str(line))
            await asyncio.sleep(60 * 5)
