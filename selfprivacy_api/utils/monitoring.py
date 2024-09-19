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
    metric_id: str
    values: List[MonitoringValue]


@strawberry.type
class MonitoringQueryError:
    error: str


@strawberry.type
class MonitoringValues:
    values: List[MonitoringValue]


@strawberry.type
class MonitoringMetrics:
    metrics: List[MonitoringMetric]


MonitoringValuesResult = Annotated[
    Union[MonitoringValues, MonitoringQueryError],
    strawberry.union("MonitoringValuesResult"),
]


MonitoringMetricsResult = Annotated[
    Union[MonitoringMetrics, MonitoringQueryError],
    strawberry.union("MonitoringMetricsResult"),
]


class MonitoringQueries:
    @staticmethod
    def _send_range_query(
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
                timeout=0.8,
            )
            if response.status_code != 200:
                return MonitoringQueryError(
                    error=f"Prometheus returned unexpected HTTP status code. Error: {response.text}. The query was {query}"
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
    def _send_query(
        query: str, result_type: Optional[str] = None
    ) -> Union[dict, MonitoringQueryError]:
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={
                    "query": query,
                },
                timeout=0.8,
            )
            if response.status_code != 200:
                return MonitoringQueryError(
                    error=f"Prometheus returned unexpected HTTP status code. Error: {response.text}. The query was {query}"
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
    def _get_time_range(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Tuple[datetime, datetime]:
        """Get the start and end time for queries."""
        if start is None:
            start = datetime.now() - timedelta(minutes=20)

        if end is None:
            end = datetime.now()

        return start, end

    @staticmethod
    def _prometheus_value_to_monitoring_value(x: Tuple[int, str]):
        return MonitoringValue(timestamp=datetime.fromtimestamp(x[0]), value=x[1])

    @staticmethod
    def _clean_slice_id(slice_id: str, clean_id: bool) -> str:
        """Slices come in form of `/slice_name.slice`, we need to remove the `.slice` and `/` part."""
        if clean_id:
            parts = slice_id.split(".")[0].split("/")
            if len(parts) > 1:
                return parts[1]
            else:
                raise ValueError(f"Incorrect format slice_id: {slice_id}")
        return slice_id

    @staticmethod
    def _prometheus_response_to_monitoring_metrics(
        response: dict, id_key: str, clean_id: bool = False
    ) -> List[MonitoringMetric]:
        if response["resultType"] == "vector":
            return list(
                map(
                    lambda x: MonitoringMetric(
                        metric_id=MonitoringQueries._clean_slice_id(
                            x["metric"].get(id_key, "/unknown.slice"),
                            clean_id=clean_id,
                        ),
                        values=[
                            MonitoringQueries._prometheus_value_to_monitoring_value(
                                x["value"]
                            )
                        ],
                    ),
                    response["result"],
                )
            )
        else:
            return list(
                map(
                    lambda x: MonitoringMetric(
                        metric_id=MonitoringQueries._clean_slice_id(
                            x["metric"].get(id_key, "/unknown.slice"), clean_id=clean_id
                        ),
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
    def _calculate_offset_and_duration(
        start: datetime, end: datetime
    ) -> Tuple[int, int]:
        """Calculate the offset and duration for Prometheus queries.
        They mast be in seconds.
        """
        offset = int((datetime.now() - end).total_seconds())
        duration = int((end - start).total_seconds())
        return offset, duration

    @staticmethod
    def cpu_usage_overall(
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

        start, end = MonitoringQueries._get_time_range(start, end)

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'

        data = MonitoringQueries._send_range_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringValues(
            values=list(
                map(
                    MonitoringQueries._prometheus_value_to_monitoring_value,
                    data["result"][0]["values"],
                )
            )
        )

    @staticmethod
    def memory_usage_overall(
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

        start, end = MonitoringQueries._get_time_range(start, end)

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = "100 - (100 * (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"

        data = MonitoringQueries._send_range_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringValues(
            values=list(
                map(
                    MonitoringQueries._prometheus_value_to_monitoring_value,
                    data["result"][0]["values"],
                )
            )
        )

    @staticmethod
    def swap_usage_overall(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: int = 60,  # seconds
    ) -> MonitoringValuesResult:
        """
        Get swap memory usage.

        Args:
            start (datetime, optional): The start time.
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): The end time.
                Defaults to current time if not provided.
            step (int): Interval in seconds for querying swap memory usage data.
        """

        start, end = MonitoringQueries._get_time_range(start, end)

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = (
            "100 - (100 * (node_memory_SwapFree_bytes / node_memory_SwapTotal_bytes))"
        )

        data = MonitoringQueries._send_range_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringValues(
            values=list(
                map(
                    MonitoringQueries._prometheus_value_to_monitoring_value,
                    data["result"][0]["values"],
                )
            )
        )

    @staticmethod
    def memory_usage_max_by_slice(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> MonitoringMetricsResult:
        """
        Get maximum memory usage for each service (i.e. systemd slice).

        Args:
            start (datetime, optional): The start time.
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): The end time.
                Defaults to current time if not provided.
        """

        start, end = MonitoringQueries._get_time_range(start, end)

        offset, duration = MonitoringQueries._calculate_offset_and_duration(start, end)

        if offset == 0:
            query = f'max_over_time((container_memory_rss{{id!~".*slice.*slice", id=~".*slice"}}+container_memory_swap{{id!~".*slice.*slice", id=~".*slice"}})[{duration}s:])'
        else:
            query = f'max_over_time((container_memory_rss{{id!~".*slice.*slice", id=~".*slice"}}+container_memory_swap{{id!~".*slice.*slice", id=~".*slice"}})[{duration}s:] offset {offset}s)'

        data = MonitoringQueries._send_query(query, result_type="vector")

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringMetrics(
            metrics=MonitoringQueries._prometheus_response_to_monitoring_metrics(
                data, "id", clean_id=True
            )
        )

    @staticmethod
    def memory_usage_average_by_slice(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> MonitoringMetricsResult:
        """
        Get average memory usage for each service (i.e. systemd slice).

        Args:
            start (datetime, optional): The start time.
                Defaults to 20 minutes ago if not provided.
            end (datetime, optional): The end time.
                Defaults to current time if not provided.
        """

        start, end = MonitoringQueries._get_time_range(start, end)

        offset, duration = MonitoringQueries._calculate_offset_and_duration(start, end)

        if offset == 0:
            query = f'avg_over_time((container_memory_rss{{id!~".*slice.*slice", id=~".*slice"}}+container_memory_swap{{id!~".*slice.*slice", id=~".*slice"}})[{duration}s:])'
        else:
            query = f'avg_over_time((container_memory_rss{{id!~".*slice.*slice", id=~".*slice"}}+container_memory_swap{{id!~".*slice.*slice", id=~".*slice"}})[{duration}s:] offset {offset}s)'

        data = MonitoringQueries._send_query(query, result_type="vector")

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringMetrics(
            metrics=MonitoringQueries._prometheus_response_to_monitoring_metrics(
                data, "id", clean_id=True
            )
        )

    @staticmethod
    def disk_usage_overall(
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

        start, end = MonitoringQueries._get_time_range(start, end)

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = """100 - (100 * sum by (device) (node_filesystem_avail_bytes{fstype!="rootfs",fstype!="ramfs",fstype!="tmpfs",mountpoint!="/efi"}) / sum by (device) (node_filesystem_size_bytes{fstype!="rootfs",fstype!="ramfs",fstype!="tmpfs",mountpoint!="/efi"}))"""

        data = MonitoringQueries._send_range_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringMetrics(
            metrics=MonitoringQueries._prometheus_response_to_monitoring_metrics(
                data, "device"
            )
        )

    @staticmethod
    def network_usage_overall(
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

        start, end = MonitoringQueries._get_time_range(start, end)

        start_timestamp = int(start.timestamp())
        end_timestamp = int(end.timestamp())

        query = """
            label_replace(rate(node_network_receive_bytes_total{device!="lo"}[5m]), "direction", "receive", "device", ".*")
            or
            label_replace(rate(node_network_transmit_bytes_total{device!="lo"}[5m]), "direction", "transmit", "device", ".*")
        """

        data = MonitoringQueries._send_range_query(
            query, start_timestamp, end_timestamp, step, result_type="matrix"
        )

        if isinstance(data, MonitoringQueryError):
            return data

        return MonitoringMetrics(
            metrics=MonitoringQueries._prometheus_response_to_monitoring_metrics(
                data, "direction"
            )
        )
