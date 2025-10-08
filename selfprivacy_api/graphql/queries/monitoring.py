import gettext

import strawberry
from strawberry.types import Info

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
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

_ = gettext.gettext

PROMETHEUS_IS_NOT_RUNNING = _("Prometheus is not running")


@strawberry.type
class CpuMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self, info: Info) -> MonitoringValuesResult:
        locale = info.context["locale"]

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(
                error=t.translate(text=PROMETHEUS_IS_NOT_RUNNING, locale=locale)
            )

        return MonitoringQueries.cpu_usage_overall(self.start, self.end, self.step)


@strawberry.type
class MemoryMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self, info: Info) -> MonitoringValuesResult:
        locale = info.context["locale"]

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(
                error=t.translate(text=PROMETHEUS_IS_NOT_RUNNING, locale=locale)
            )

        return MonitoringQueries.memory_usage_overall(self.start, self.end, self.step)

    @strawberry.field
    def swap_usage_overall(self, info: Info) -> MonitoringValuesResult:
        locale = info.context["locale"]

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(
                error=t.translate(text=PROMETHEUS_IS_NOT_RUNNING, locale=locale)
            )

        return MonitoringQueries.swap_usage_overall(self.start, self.end, self.step)

    @strawberry.field
    def average_usage_by_service(self, info: Info) -> MonitoringMetricsResult:
        locale = info.context["locale"]

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(
                error=t.translate(text=PROMETHEUS_IS_NOT_RUNNING, locale=locale)
            )

        return MonitoringQueries.memory_usage_average_by_slice(self.start, self.end)

    @strawberry.field
    def max_usage_by_service(self, info: Info) -> MonitoringMetricsResult:
        locale = info.context["locale"]

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(
                error=t.translate(text=PROMETHEUS_IS_NOT_RUNNING, locale=locale)
            )

        return MonitoringQueries.memory_usage_max_by_slice(self.start, self.end)


@strawberry.type
class DiskMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self, info: Info) -> MonitoringMetricsResult:
        locale = info.context["locale"]

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(
                error=t.translate(text=PROMETHEUS_IS_NOT_RUNNING, locale=locale)
            )

        return MonitoringQueries.disk_usage_overall(self.start, self.end, self.step)


@strawberry.type
class NetworkMonitoring:
    start: Optional[datetime]
    end: Optional[datetime]
    step: int

    @strawberry.field
    def overall_usage(self, info: Info) -> MonitoringMetricsResult:
        locale = info.context["locale"]

        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(
                error=t.translate(text=PROMETHEUS_IS_NOT_RUNNING, locale=locale)
            )

        return MonitoringQueries.network_usage_overall(self.start, self.end, self.step)


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
