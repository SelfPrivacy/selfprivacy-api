import strawberry
from typing import Optional
from datetime import datetime
from selfprivacy_api.models.services import ServiceStatus
from selfprivacy_api.services.prometheus import Prometheus
from selfprivacy_api.utils.monitoring import MonitoringQueries, MonitoringQueryError, MonitoringResponse


@strawberry.type
class Monitoring:
    @strawberry.field
    def disk_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.disk_usage(start, end, step)

    @strawberry.field
    def memory_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.memory_usage(start, end, step)

    @strawberry.field
    def cpu_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.cpu_usage(start, end, step)

    @strawberry.field
    def network_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        if Prometheus().get_status() != ServiceStatus.ACTIVE:
            return MonitoringQueryError(error="Prometheus is not running")

        return MonitoringQueries.cpu_usage(start, end, step)
