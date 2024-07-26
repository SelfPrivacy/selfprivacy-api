"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
import requests

import strawberry
from strawberry.scalars import JSON

from dataclasses import dataclass
from typing import Optional, Annotated, Union
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9001"


@strawberry.type
@dataclass
class MonitoringQueryResult:
    result_type: str
    result: JSON


@strawberry.type
class MonitoringQueryError:
    error: str


MonitoringResponse = Annotated[
    Union[MonitoringQueryResult, MonitoringQueryError],
    strawberry.union("MonitoringQueryResponse"),
]


class MonitoringQueries:
    @staticmethod
    def _send_query(query: str, start: int, end: int, step: int) -> MonitoringResponse:
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params={
                    "query": query,
                    "start": start,
                    "end": end,
                    "step": step,
                },
            )
            if response.status_code != 200:
                return MonitoringQueryError(
                    error="Prometheus returned unexpected HTTP status code"
                )
            json = response.json()
            return MonitoringQueryResult(
                result_type=json["data"]["resultType"], result=json["data"]["result"]
            )
        except Exception as error:
            return MonitoringQueryError(
                error=f"Prometheus request failed! Error: {str(error)}"
            )

    @staticmethod
    def cpu_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringResponse:
        """
        Get CPU information.

        Args:
            start (datetime, optional): The start time.
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): The end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying disk usage data.
        """

        if start is None:
            start = datetime.now() - timedelta(minutes=20)

        if end is None:
            end = datetime.now()

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'

        return MonitoringQueries._send_query(
            query,
            start_timestamp,
            end_timestamp,
            step,
        )

    @staticmethod
    def memory_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringResponse:
        """
        Get memory usage.

        Args:
            start (datetime, optional): The start time.
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): The end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying memory usage data.
        """

        if start is None:
            start = datetime.now() - timedelta(minutes=20)

        if end is None:
            end = datetime.now()

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = "100 - (100 * (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"

        return MonitoringQueries._send_query(
            query,
            start_timestamp,
            end_timestamp,
            step,
        )

    @staticmethod
    def disk_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringResponse:
        """
        Get disk usage information.

        Args:
            start (datetime, optional): The start time.
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): The end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying disk usage data.
        """

        if start is None:
            start = datetime.now() - timedelta(minutes=20)

        if end is None:
            end = datetime.now()

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = """100 - (100 * sum by (device) (node_filesystem_avail_bytes{fstype!="rootfs"}) / sum by (device) (node_filesystem_size_bytes{fstype!="rootfs"}))"""

        return MonitoringQueries._send_query(
            query,
            start_timestamp,
            end_timestamp,
            step,
        )

    @staticmethod
    def network_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringResponse:
        """
        Get network usage information for both download and upload.

        Args:
            start (datetime, optional): The start time.
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): The end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying network data.
        """

        if start is None:
            start = datetime.now() - timedelta(minutes=20)

        if end is None:
            end = datetime.now()

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = """
        (
            sum(rate(node_network_receive_bytes_total{device!="lo"}[5m])) as download,
            sum(rate(node_network_transmit_bytes_total{device!="lo"}[5m])) as upload
        )
        """

        return MonitoringQueries._send_query(
            query,
            start_timestamp,
            end_timestamp,
            step,
        )
