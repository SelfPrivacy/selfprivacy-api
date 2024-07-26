import strawberry
from typing import Optional
from datetime import datetime
from selfprivacy_api.utils.prometheus import PrometheusQueries, Response


@strawberry.type
class Monitoring:
    @strawberry.field
    def disk_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> Response:
        return PrometheusQueries.disk_usage(start, end, step)

    @strawberry.field
    def memory_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> Response:
        return PrometheusQueries.memory_usage(start, end, step)

    @strawberry.field
    def cpu_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> Response:
        return PrometheusQueries.cpu_usage(start, end, step)

    @strawberry.field
    def network_usage(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,
    ) -> Response:
        return PrometheusQueries.cpu_usage(start, end, step)
