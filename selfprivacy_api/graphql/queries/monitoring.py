import strawberry
from typing import Optional
from datetime import datetime
from selfprivacy_api.utils.prometheus import MonitoringQueries, MonitoringResponse


@strawberry.type
class Monitoring:
    @strawberry.field
    def disk_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        return MonitoringQueries.disk_usage(start, end, step)

    @strawberry.field
    def memory_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        return MonitoringQueries.memory_usage(start, end, step)

    @strawberry.field
    def cpu_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        return MonitoringQueries.cpu_usage(start, end, step)

    @strawberry.field
    def network_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> MonitoringResponse:
        return MonitoringQueries.cpu_usage(start, end, step)
