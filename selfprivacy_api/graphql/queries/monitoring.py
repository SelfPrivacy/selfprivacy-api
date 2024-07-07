import strawberry

from selfprivacy_api.utils.prometheus import PrometheusQueries


@strawberry.type
class Monitoring:
    @strawberry.field
    def disks_usage():
        return PrometheusQueries.disks_usage()

    @strawberry.field
    def cpu_usage():
        return PrometheusQueries.cpu_usage()
