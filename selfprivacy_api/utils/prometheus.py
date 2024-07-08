"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
import requests
import strawberry
from dataclasses import dataclass
from typing import Optional
from strawberry.scalars import JSON
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9001"


@strawberry.type
@dataclass
class PrometheusQueryResult:
    result_type: str
    result: JSON


class PrometheusQueries:
    @staticmethod
    def _send_query(query: str, start: int, end: int, step: int):
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={
                    "query": query,
                    "start": start,
                    "end": end,
                    "step": step,
                },
            )
            if response.status_code != 200:
                raise Exception("Prometheus returned unexpected HTTP status code")
            json = response.json()
            return PrometheusQueryResult(
                result_type=json.result_type, result=json.result
            )
        except Exception as error:
            raise Exception("Prometheus request failed! " + str(error))

    @staticmethod
    def cpu_usage(
        start: Optional[int] = None,
        end: Optional[int] = None,
        step: int = 60,  # seconds
    ) -> PrometheusQueryResult:
        """
        Get CPU information.

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

        return PrometheusQueries._send_query(query, start, end, step)

    @staticmethod
    def memory_usage(
        start: Optional[int] = None,
        end: Optional[int] = None,
        step: int = 60,  # seconds
    ) -> PrometheusQueryResult:
        """
        Get memory usage.

        Args:
            start (int, optional): Unix timestamp indicating the start time.
                Defaults to 20 minutes ago if not provided.
            end (int, optional): Unix timestamp indicating the end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying memory usage data.
        """

        if not start:
            start = int((datetime.now() - timedelta(minutes=20)).timestamp())

        if not end:
            end = int(datetime.now().timestamp())

        query = "100 - (100 * (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"

        return PrometheusQueries._send_query(query, start, end, step)

    @staticmethod
    def disk_usage(
        start: Optional[int] = None,
        end: Optional[int] = None,
        step: int = 60,  # seconds
    ) -> PrometheusQueryResult:
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

        return PrometheusQueries._send_query(query, start, end, step)
