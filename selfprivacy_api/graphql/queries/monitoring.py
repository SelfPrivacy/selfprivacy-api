import logging
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

logger = logging.getLogger(__name__)


@strawberry.type
class CpuMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self) -> MonitoringValuesResult:
        logging.info("CpuMonitoring collecting...")

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        data = MonitoringQueries.cpu_usage_overall(self.start, self.end, self.step)
        logging.info("CpuMonitoring DONE")
        return data


@strawberry.type
class MemoryMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self) -> MonitoringValuesResult:
        logging.info("MemoryMonitoring overall_usage collecting...")

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        data = MonitoringQueries.memory_usage_overall(self.start, self.end, self.step)
        logging.info("MemoryMonitoring overall_usage DONE")
        return data

    @strawberry.field
    def swap_usage_overall(self) -> MonitoringValuesResult:
        logging.info("MemoryMonitoring swap_usage_overall collecting...")

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        data = MonitoringQueries.swap_usage_overall(self.start, self.end, self.step)
        logging.info("MemoryMonitoring swap_usage_overall DONE")
        return data

    @strawberry.field
    def average_usage_by_service(self) -> MonitoringMetricsResult:
        logging.info("MemoryMonitoring average_usage_by_service collecting...")

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        data = MonitoringQueries.memory_usage_average_by_slice(self.start, self.end)
        logging.info("MemoryMonitoring swap_usage_overall DONE")
        return data

    @strawberry.field
    def max_usage_by_service(self) -> MonitoringMetricsResult:
        logging.info("MemoryMonitoring max_usage_by_service collecting...")

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        data = MonitoringQueries.memory_usage_max_by_slice(self.start, self.end)
        logging.info("MemoryMonitoring swap_usage_overall DONE")
        return data


@strawberry.type
class DiskMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self) -> MonitoringMetricsResult:
        logging.info("DiskMonitoring collecting...")

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        data = MonitoringQueries.disk_usage_overall(self.start, self.end, self.step)
        logging.info("DiskMonitoring DONE")
        return data


@strawberry.type
class NetworkMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self) -> MonitoringMetricsResult:
        logging.info("NetworkMonitoring collecting...")

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        data = MonitoringQueries.network_usage_overall(self.start, self.end, self.step)
        logging.info("NetworkMonitoring DONE")
        return data


@strawberry.type
class Monitoring:
    @strawberry.field
    def cpu_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> CpuMonitoring:
        return CpuMonitoring(start=start, end=end, step=step)

    @strawberry.field
    def memory_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MemoryMonitoring:
        return MemoryMonitoring(start=start, end=end, step=step)

    @strawberry.field
    def disk_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> DiskMonitoring:
        return DiskMonitoring(start=start, end=end, step=step)

    @strawberry.field
    def network_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> NetworkMonitoring:
        return NetworkMonitoring(start=start, end=end, step=step)
