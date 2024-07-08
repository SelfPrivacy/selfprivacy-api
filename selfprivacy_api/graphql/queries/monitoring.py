import strawberry

from selfprivacy_api.utils.prometheus import PrometheusQueries, PrometheusQueryResult


@strawberry.type
class Monitoring:
    @strawberry.field
    def disk_usage() -> PrometheusQueryResult:
        return PrometheusQueries.disk_usage()

    @strawberry.field
    def memory_usage() -> PrometheusQueryResult:
        return PrometheusQueries.memory_usage()

    @strawberry.field
    def cpu_usage() -> PrometheusQueryResult:
        return PrometheusQueries.cpu_usage()
