"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
import typing
from typing import Optional

import strawberry
import requests

# TODO: добавить файл в schema.py

PROMETHEUS_URL = "http://localhost:9090"


@strawberry.type
class MonitoringInfo:
    """ """

    http_response: int
    output: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class Monitoring:
    """GraphQL queries to get prometheus monitoring information."""

    def _send_request(self, endpoint="/api/v1/query", query=None) -> MonitoringInfo:
        try:
            if query:
                response = requests.get(
                    f"{PROMETHEUS_URL}{endpoint}", params={"query": query}
                )
            else:
                response = requests.get(f"{PROMETHEUS_URL}{endpoint}")

            return MonitoringInfo(
                http_response=response.status_code,
                output=(
                    json.dumps(response.json()) if response.status_code == 200 else None
                ),
            )
        except requests.RequestException as error:
            return MonitoringInfo(
                http_response=500,  # копилот предложил использовать тут 500
                error=str(error),
            )

    @strawberry.field
    def status(self) -> MonitoringInfo:
        """Get status"""
        endpoint = "/api/v1/status/runtimeinfo"
        return _send_request(endpoint=endpoint)

    @strawberry.field
    def build(self) -> MonitoringInfo:
        """Get build information"""
        endpoint = "/api/v1/status/buildinfo"
        return _send_request(endpoint=endpoint)

    @strawberry.field
    def cpu_usage(self) -> MonitoringInfo:
        """Get CPU information"""
        query = """100 - (avg by (instance) (irate(node_cpu_seconds_total{job="node",mode="idle"}[5m])) * 100)"""
        # TODO: не представляю рабочий ли этот запрос вообще
        # https://overflow.hostux.net/questions/34923788/prometheus-convert-cpu-user-seconds-to-cpu-usage
        # ему бы еще сделать кастомные минуты, чтоб разное время указывать, но так чтоб нельзя было инжектить
        return _send_request(query=query)

    def disks_usage(): ...
