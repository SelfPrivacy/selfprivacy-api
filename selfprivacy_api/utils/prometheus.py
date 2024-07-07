"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
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
        start: Optional[int] = None,
        end: Optional[int] = None,
        step: int = 60,  # seconds
    ) -> PrometheusInfo:
        """Get CPU information,.

        Args:
            start (int, optional): Unix timestamp indicating the start time.
                Defaults to 20 minutes ago if not provided.
            end (int, optional): Unix timestamp indicating the end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying disk usage data.
        """

        if not start:
            start = int((datetime.now() - timedelta(minutes=20)).timestamp())

        if not end:
            end = int(datetime.now().timestamp())

        query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'

        params = {"query": query, "start": start, "end": end, "step": step}

        return PrometheusQueries._send_request(params=params)

    @staticmethod
    def disk_usage(
        start: Optional[int] = None,
        end: Optional[int] = None,
        step: int = 60,  # seconds
    ) -> PrometheusInfo:
        """
        Get disk usage information.

        Args:
            start (int, optional): Unix timestamp indicating the start time.
                Defaults to 20 minutes ago if not provided.
            end (int, optional): Unix timestamp indicating the end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying disk usage data.
        """

        if not start:
            start = int((datetime.now() - timedelta(minutes=20)).timestamp())

        if not end:
            end = int(datetime.now().timestamp())

        query = '100 - (100 * ((node_filesystem_avail_bytes{mountpoint="/",fstype!="rootfs"} )  / (node_filesystem_size_bytes{mountpoint="/",fstype!="rootfs"}) ))'

        params = {"query": query, "start": start, "end": end, "step": step}

        return PrometheusQueries._send_request(params=params)
