"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
import time

import typing
from typing import Optional

PROMETHEUS_URL = "http://localhost:9090"


class PrometheusInfo:
    """ """

    http_response: int
    output: Optional[typing.Dict] = None
    error: Optional[str] = None


class PrometheusQueries:
    @staticmethod
    def _send_request(endpoint="/api/v1/query", params=None) -> PrometheusInfo:
        try:
            response = requests.get(f"{PROMETHEUS_URL}{endpoint}", params=params)
            return PrometheusInfo(
                http_response=response.status_code,
                output=(response.json() if response.status_code == 200 else None),
            )
        except requests.RequestException as error:
            return PrometheusInfo(
                http_response=500,
                error=str(error),
            )

    @staticmethod
    def cpu_usage() -> PrometheusInfo:
        """Get CPU information"""
        start = int((datetime.now() - timedelta(minutes=20)).timestamp())
        end = int(datetime.now().timestamp())
        query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'

        params = {"query": query, "start": start, "end": end, "step": 60}

        return self._send_request(params=params)

    @staticmethod
    def disk_usage() -> PrometheusInfo:
        """Get disk usage information"""
        start = int((datetime.now() - timedelta(minutes=20)).timestamp())
        end = int(datetime.now().timestamp())
        query = 'rate(node_filesystem_size_bytes{mountpoint="/"}[5m])'

        params = {"query": query, "start": start, "end": end, "step": 60}
        return self._send_request(params=params)
