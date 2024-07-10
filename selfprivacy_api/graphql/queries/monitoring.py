import strawberry
from typing import Optional
from selfprivacy_api.utils.prometheus import PrometheusQueries, PrometheusQueryResult


@strawberry.type
class Monitoring:
    @staticmethod
    @strawberry.field
    def disk_usage(start: Optional[int] = None, end: Optional[int] = None, step: int = 60) -> PrometheusQueryResult:
        return PrometheusQueries.disk_usage(start, end, step)

    @staticmethod
    @strawberry.field
    def memory_usage(start: Optional[int] = None, end: Optional[int] = None, step: int = 60) -> PrometheusQueryResult:
        return PrometheusQueries.memory_usage(start, end, step)

    @staticmethod
    @strawberry.field
    def cpu_usage(start: Optional[int] = None, end: Optional[int] = None, step: int = 60) -> PrometheusQueryResult:
        c = PrometheusQueries.cpu_usage(start, end, step)
        return c
        return PrometheusQueries.cpu_usage(start, end, step)
