"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
import requests

import strawberry
from strawberry.scalars import JSON

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9001"


@strawberry.type
@dataclass
class PrometheusQueryResult:
    result_type: str
    result: JSON


class PrometheusQueries:
    @staticmethod
    def _send_query(query: str, start: datetime, end: datetime, step: int):
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params={
                    "query": query,
                    "start": int(start.timestamp()),
                    "end": int(start.timestamp()),
                    "step": step,
                },
            )
            if response.status_code != 200:
                raise Exception("Prometheus returned unexpected HTTP status code")
            json = response.json()
            if json["status"] != "success":
                raise Exception("Prometheus returned unexpected status")
            result = json["data"]
            return PrometheusQueryResult(
                result_type=result["resultType"], result=result["result"]
            )
        except Exception as error:
            raise Exception("Prometheus request failed! " + str(error))

    @staticmethod
    def cpu_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> PrometheusQueryResult:
        """
        Get CPU information.

        Args:
            start (datetime, optional): timestamp indicating the start time of metrics to fetch
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): timestamp indicating the end time of metrics to fetch
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying disk usage data.
        """

        if not start:
            start = datetime.now() - timedelta(minutes=20)

        if not end:
            end = datetime.now()

        query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'

        return PrometheusQueries._send_query(query, start, end, step)

    @staticmethod
    def memory_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> PrometheusQueryResult:
        """
        Get memory usage.

        Args:
            start (datetime, optional): timestamp indicating the start time of metrics to fetch
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): timestamp indicating the end time of metrics to fetch
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying memory usage data.
        """

        if not start:
            start = datetime.now() - timedelta(minutes=20)

        if not end:
            end = datetime.now()

        query = "100 - (100 * (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"

        return PrometheusQueries._send_query(query, start, end, step)

    @staticmethod
    def disk_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> PrometheusQueryResult:
        """
        Get disk usage information.

        Args:
            start (datetime, optional): timestamp indicating the start time of metrics to fetch
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): timestamp indicating the end time of metrics to fetch
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying disk usage data.
        """

        if not start:
            start = datetime.now() - timedelta(minutes=20)

        if not end:
            end = datetime.now()

        query = '100 - (100 * ((node_filesystem_avail_bytes{mountpoint="/",fstype!="rootfs"} )  / (node_filesystem_size_bytes{mountpoint="/",fstype!="rootfs"}) ))'

        return PrometheusQueries._send_query(query, start, end, step)
