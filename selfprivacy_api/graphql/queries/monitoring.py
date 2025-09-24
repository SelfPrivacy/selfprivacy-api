import strawberry
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


@strawberry.type
class CpuMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringValuesResult:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.cpu_usage_overall(self.start, self.end, self.step)


@strawberry.type
class MemoryMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringValuesResult:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.memory_usage_overall(self.start, self.end, self.step)

    @strawberry.field
    async def swap_usage_overall(self) -> MonitoringValuesResult:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.swap_usage_overall(self.start, self.end, self.step)

    @strawberry.field
    async def average_usage_by_service(self) -> MonitoringMetricsResult:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.memory_usage_average_by_slice(self.start, self.end)

    @strawberry.field
    async def max_usage_by_service(self) -> MonitoringMetricsResult:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.memory_usage_max_by_slice(self.start, self.end)


@strawberry.type
class DiskMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringMetricsResult:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.disk_usage_overall(self.start, self.end, self.step)


@strawberry.type
class NetworkMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    async def overall_usage(self) -> MonitoringMetricsResult:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.network_usage_overall(self.start, self.end, self.step)


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
