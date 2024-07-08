import strawberry

from selfprivacy_api.utils.prometheus import PrometheusQueries


@strawberry.type
class Monitoring:
    @strawberry.field
    def disk_usage():
        return PrometheusQueries.disk_usage()

    @strawberry.field
    def memory_usage():
        return PrometheusQueries.memory_usage()

    @strawberry.field
    def cpu_usage():
        return PrometheusQueries.cpu_usage()
