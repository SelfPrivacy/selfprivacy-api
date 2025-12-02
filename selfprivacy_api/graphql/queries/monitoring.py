import strawberry
from opentelemetry import trace
from typing import Optional
from datetime import datetime
from selfprivacy_api.models.services import ServiceStatus
from selfprivacy_api.services.prometheus import Prometheus
from selfprivacy_api.utils.monitoring import (
    MonitoringQueries,
    MonitoringQueryError,
    MonitoringValuesResult,
    MonitoringMetricsResult,
)

tracer = trace.get_tracer(__name__)


@strawberry.type
class CpuMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringValuesResult:
        with tracer.start_as_current_span("CpuMonitoring.overall_usage"):
            if await Prometheus().get_status() != ServiceStatus.ACTIVE:
                return MonitoringQueryError(error="Prometheus is not running")

            return await MonitoringQueries.cpu_usage_overall(
                self.start, self.end, self.step
            )


@strawberry.type
class MemoryMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringValuesResult:
        with tracer.start_as_current_span("MemoryMonitoring.overall_usage"):
            if await Prometheus().get_status() != ServiceStatus.ACTIVE:
                return MonitoringQueryError(error="Prometheus is not running")

            return await MonitoringQueries.memory_usage_overall(
                self.start, self.end, self.step
            )

    @strawberry.field
    async def swap_usage_overall(self) -> MonitoringValuesResult:
        with tracer.start_as_current_span("MemoryMonitoring.swap_usage_overall"):
            if await Prometheus().get_status() != ServiceStatus.ACTIVE:
                return MonitoringQueryError(error="Prometheus is not running")

            return await MonitoringQueries.swap_usage_overall(
                self.start, self.end, self.step
            )

    @strawberry.field
    async def average_usage_by_service(self) -> MonitoringMetricsResult:
        with tracer.start_as_current_span("MemoryMonitoring.average_usage_by_service"):
            if await Prometheus().get_status() != ServiceStatus.ACTIVE:
                return MonitoringQueryError(error="Prometheus is not running")

            return await MonitoringQueries.memory_usage_average_by_slice(
                self.start, self.end
            )

    @strawberry.field
    async def max_usage_by_service(self) -> MonitoringMetricsResult:
        with tracer.start_as_current_span("MemoryMonitoring.max_usage_by_service"):
            if await Prometheus().get_status() != ServiceStatus.ACTIVE:
                return MonitoringQueryError(error="Prometheus is not running")

            return await MonitoringQueries.memory_usage_max_by_slice(
                self.start, self.end
            )


@strawberry.type
class DiskMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringMetricsResult:
        with tracer.start_as_current_span("DiskMonitoring.overall_usage"):
            if await Prometheus().get_status() != ServiceStatus.ACTIVE:
                return MonitoringQueryError(error="Prometheus is not running")

            return await MonitoringQueries.disk_usage_overall(
                self.start, self.end, self.step
            )


@strawberry.type
class NetworkMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringMetricsResult:
        with tracer.start_as_current_span("NetworkMonitoring.overall_usage"):
            if await Prometheus().get_status() != ServiceStatus.ACTIVE:
                return MonitoringQueryError(error="Prometheus is not running")

            return await MonitoringQueries.network_usage_overall(
                self.start, self.end, self.step
            )


@strawberry.type
class Monitoring:
    @strawberry.field
    async def cpu_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> CpuMonitoring:
        return CpuMonitoring(start=start, end=end, step=step)

    @strawberry.field
    async def memory_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MemoryMonitoring:
        return MemoryMonitoring(start=start, end=end, step=step)

    @strawberry.field
    async def disk_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> DiskMonitoring:
        return DiskMonitoring(start=start, end=end, step=step)

    @strawberry.field
    async def network_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> NetworkMonitoring:
        return NetworkMonitoring(start=start, end=end, step=step)
