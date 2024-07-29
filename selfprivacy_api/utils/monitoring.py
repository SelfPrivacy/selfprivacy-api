"""Prometheus monitoring queries."""

# pylint: disable=too-few-public-methods
import requests

import strawberry

from dataclasses import dataclass
from typing import Optional, Annotated, Union, List, Tuple
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9001"


@strawberry.type
@dataclass
class MonitoringValue:
    timestamp: datetime
    value: str


@strawberry.type
@dataclass
class MonitoringMetric:
    id: str
    values: List[MonitoringValue]


@strawberry.type
class MonitoringQueryError:
    error: str


MonitoringValuesResult = Annotated[
    Union[List[MonitoringValue], MonitoringQueryError],
    strawberry.union("MonitoringValuesResult"),
]


MonitoringMetricsResult = Annotated[
    Union[List[MonitoringMetric], MonitoringQueryError],
    strawberry.union("MonitoringMetricsResult"),
]


class MonitoringQueries:
    @staticmethod
    def _send_query(
        query: str, start: int, end: int, step: int, result_type: Optional[str] = None
    ) -> Union[dict, MonitoringQueryError]:
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
            if result_type and json["data"]["resultType"] != result_type:
                return MonitoringQueryError(
                    error="Unexpected resultType returned from Prometheus, request failed"
                )
            return json["data"]
        except Exception as error:
            return MonitoringQueryError(
                error=f"Prometheus request failed! Error: {str(error)}"
            )

    @staticmethod
    def _prometheus_value_to_monitoring_value(x: Tuple[int, str]):
        return MonitoringValue(timestamp=datetime.fromtimestamp(x[0]), value=x[1])

    @staticmethod
    def _prometheus_response_to_monitoring_metrics(
        response: dict, id_key: str
    ) -> List[MonitoringMetric]:
        return list(
            map(
                lambda x: MonitoringMetric(
                    id=x["metric"][id_key],
                    values=list(
                        map(
                            MonitoringQueries._prometheus_value_to_monitoring_value,
                            x["values"],
                        )
                    ),
                ),
                response["result"],
            )
        )

    @staticmethod
    def cpu_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringValuesResult:
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

        data = MonitoringQueries._send_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return list(
            map(
                MonitoringQueries._prometheus_value_to_monitoring_value,
                data["result"][0]["values"],
            )
        )

    @staticmethod
    def memory_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringValuesResult:
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

        data = MonitoringQueries._send_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return list(
            map(
                MonitoringQueries._prometheus_value_to_monitoring_value,
                data["result"][0]["values"],
            )
        )

    @staticmethod
    def disk_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringMetricsResult:
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

        data = MonitoringQueries._send_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringQueries._prometheus_response_to_monitoring_metrics(
            data, "device"
        )

    @staticmethod
    def network_usage(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringMetricsResult:
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

        data = MonitoringQueries._send_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringQueries._prometheus_response_to_monitoring_metrics(
            data, "device"
        )
