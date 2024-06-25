"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
import time
import requests
from typing import Optional, Dict
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9001"


class PrometheusInfo:
    """ """

    http_response: int
    output: Optional[Dict] = None
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
    def cpu_usage(
        start: int = int((datetime.now() - timedelta(minutes=20)).timestamp()),
        end: int = int(datetime.now().timestamp()),
        step: int = 60,
    ) -> PrometheusInfo:
        """Get CPU information"""

        query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'

        params = {"query": query, "start": start, "end": end, "step": step}

        return self._send_request(params=params)

    @staticmethod
    def disk_usage(
        start: int = int((datetime.now() - timedelta(minutes=20)).timestamp()),
        end: int = int(datetime.now().timestamp()),
        step: int = 60,
    ) -> PrometheusInfo:
        """Get disk usage information"""
        query = '100 - (100 * ((node_filesystem_avail_bytes{mountpoint="/",fstype!="rootfs"} )  / (node_filesystem_size_bytes{mountpoint="/",fstype!="rootfs"}) ))'

        params = {"query": query, "start": start, "end": end, "step": step}
        return self._send_request(params=params)
