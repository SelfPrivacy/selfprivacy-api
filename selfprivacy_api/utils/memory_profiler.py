import asyncio
import tracemalloc
import logging

from selfprivacy_api.utils.otel import OTEL_ENABLED

from opentelemetry import metrics

size_threshold = 1024 * (1024 / 2)  # 0.5Mb

logger = logging.getLogger(__name__)


async def memory_profiler_task():
    if not OTEL_ENABLED or not tracemalloc.is_tracing():
        return

    meter = metrics.get_meter("selfprivacy_memory_profiler")

    allocation_size_gauge = meter.create_gauge(
        name="sp_api_allocation_size_by_line",
        description="Memory allocation sizes attributed to code lines",
        unit="By",
    )
    allocation_count_gauge = meter.create_gauge(
        name="sp_api_allocation_count_by_line",
        description="Number of allocations attributed to code lines",
        unit="{allocations}",
    )

    while True:
        snapshot = tracemalloc.take_snapshot()

        stats = snapshot.statistics("lineno")[:50]

        for stat in [s for s in stats if s.size > size_threshold]:
            file = stat.traceback[0].filename if stat.traceback else "unknown"
            line = stat.traceback[0].lineno if stat.traceback else 0
            allocation_size_gauge.set(
                stat.size, attributes={"file": file, "line": line}
            )
            allocation_count_gauge.set(
                stat.count, attributes={"file": file, "line": line}
            )

        await asyncio.sleep(60 * 5)
