# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

from datetime import datetime
from typing import Optional
import pytest

from selfprivacy_api.models.services import ServiceStatus

from tests.test_graphql.common import (
    assert_empty,
    get_data,
)


@pytest.fixture
def mock_get_status_active(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.queries.monitoring.Prometheus.get_status",
        return_value=ServiceStatus.ACTIVE,
    )
    return mock


@pytest.fixture
def mock_send_range_query(request, mocker):
    param = request.param

    async def send_query(
        query: str, start: int, end: int, step: int, result_type: Optional[str] = None
    ):
        return {
            "resultType": "matrix",
            "result": list(
                map(
                    lambda x: {
                        "metric": {param[0]: f"metric-{x}"},
                        "values": [[0, "zero"]],
                    },
                    range(0, param[1]),
                )
            ),
        }

    mock = mocker.patch(
        "selfprivacy_api.utils.monitoring.MonitoringQueries._send_range_query",
        send_query,
    )

    return mock


@pytest.fixture
def mock_send_query(request, mocker):
    param = request.param

    async def send_query(query: str, result_type: Optional[str] = None):
        return {
            "resultType": "matrix",
            "result": list(
                map(
                    lambda x: {
                        "metric": {param[0]: f"metric-{x}"},
                        "values": [[0, f"/slice_name_{x}.slice"]],
                    },
                    range(0, param[1]),
                )
            ),
        }

    mock = mocker.patch(
        "selfprivacy_api.utils.monitoring.MonitoringQueries._send_query",
        send_query,
    )

    return mock


# ....


CPU_USAGE_QUERY = """
query {
  monitoring {
    cpuUsage {
      start
      end
      step
      overallUsage {
        ... on MonitoringValues {
          values {
            timestamp
            value
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
    }
  }
}
"""

CPU_USAGE_QUERY_WITH_OPTIONS = """
query Query($end: DateTime, $start: DateTime, $step: Int) {
  monitoring {
    cpuUsage(end: $end, start: $start, step: $step) {
      end
      overallUsage {
        ... on MonitoringValues {
          values {
            timestamp
            value
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      start
      step
    }
  }
}
"""

MEMORY_USAGE_QUERY = """
query Query {
  monitoring {
    memoryUsage {
      averageUsageByService {
        ... on MonitoringMetrics {
          metrics {
            metricId
            values {
              timestamp
              value
            }
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      end
      maxUsageByService {
        ... on MonitoringMetrics {
          metrics {
            metricId
            values {
              timestamp
              value
            }
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      overallUsage {
        ... on MonitoringValues {
          values {
            timestamp
            value
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      swapUsageOverall {
        ... on MonitoringValues {
          values {
            timestamp
            value
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      start
      step
    }
  }
}
"""

MEMORY_USAGE_QUERY_WITH_OPTIONS = """
query Query($end: DateTime, $start: DateTime, $step: Int) {
  monitoring {
    memoryUsage(end: $end, start: $start, step: $step) {
      averageUsageByService {
        ... on MonitoringMetrics {
          metrics {
            metricId
            values {
              timestamp
              value
            }
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      end
      maxUsageByService {
        ... on MonitoringMetrics {
          metrics {
            metricId
            values {
              timestamp
              value
            }
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      overallUsage {
        ... on MonitoringValues {
          values {
            timestamp
            value
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      swapUsageOverall {
        ... on MonitoringValues {
          values {
            timestamp
            value
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      start
      step
    }
  }
}
"""

NETWORK_USAGE_QUERY = """
query Query {
  monitoring {
    networkUsage {
      end
      start
      step
      overallUsage {
        ... on MonitoringMetrics {
          metrics {
            metricId
            values {
              timestamp
              value
            }
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
    }
  }
}
"""

NETWORK_USAGE_QUERY_WITH_OPTIONS = """
query Query($end: DateTime, $start: DateTime, $step: Int) {
  monitoring {
    networkUsage(end: $end, start: $start, step: $step) {
      end
      overallUsage {
        ... on MonitoringMetrics {
          metrics {
            metricId
            values {
              timestamp
              value
            }
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      start
      step
    }
  }
}
"""

DISK_USAGE_QUERY = """
query Query {
  monitoring {
    diskUsage {
      start
      end
      step
      overallUsage {
        ... on MonitoringMetrics {
            metrics {
              metricId
              values {
                timestamp
                value
              }
            }
        }
        ... on MonitoringQueryError {
          error
        }
      }
    }
  }
}
"""

DISK_USAGE_QUERY_WITH_OPTIONS = """
query Query($end: DateTime, $start: DateTime, $step: Int) {
  monitoring {
    diskUsage(end: $end, start: $start, step: $step) {
      end
      overallUsage {
        ... on MonitoringMetrics {
          metrics {
            metricId
            values {
              timestamp
              value
            }
          }
        }
        ... on MonitoringQueryError {
          error
        }
      }
      start
      step
    }
  }
}
"""


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
def test_graphql_get_disk_usage(
    client,
    authorized_client,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={"query": DISK_USAGE_QUERY},
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "diskUsage": {
                "start": None,
                "end": None,
                "step": 60,
                "overallUsage": {
                    "metrics": [
                        {
                            "metricId": "metric-0",
                            "values": [
                                {"timestamp": "1970-01-01T00:00:00", "value": "zero"}
                            ],
                        },
                        {
                            "metricId": "metric-1",
                            "values": [
                                {"timestamp": "1970-01-01T00:00:00", "value": "zero"}
                            ],
                        },
                    ]
                },
            }
        }
    }


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
def test_graphql_get_disk_usage_with_options(
    client,
    authorized_client,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": DISK_USAGE_QUERY_WITH_OPTIONS,
            "variables": {
                "start": datetime.fromtimestamp(1720136108).isoformat(),
                "end": datetime.fromtimestamp(1720137319).isoformat(),
                "step": 90,
            },
        },
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "diskUsage": {
                "start": "2024-07-04T23:35:08",
                "end": "2024-07-04T23:55:19",
                "step": 90,
                "overallUsage": {
                    "metrics": [
                        {
                            "metricId": "metric-0",
                            "values": [
                                {"timestamp": "1970-01-01T00:00:00", "value": "zero"}
                            ],
                        },
                        {
                            "metricId": "metric-1",
                            "values": [
                                {"timestamp": "1970-01-01T00:00:00", "value": "zero"}
                            ],
                        },
                    ]
                },
            }
        }
    }


def test_graphql_get_disk_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": DISK_USAGE_QUERY},
    )
    assert_empty(response)


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
@pytest.mark.parametrize("mock_send_query", [["device", 2]], indirect=True)
def test_graphql_get_memory_usage(
    client,
    authorized_client,
    mock_send_query,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={"query": MEMORY_USAGE_QUERY},
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "memoryUsage": {
                "averageUsageByService": {
                    "metrics": [
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_0.slice",
                                },
                            ],
                        },
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_1.slice",
                                },
                            ],
                        },
                    ],
                },
                "end": None,
                "maxUsageByService": {
                    "metrics": [
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_0.slice",
                                },
                            ],
                        },
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_1.slice",
                                },
                            ],
                        },
                    ],
                },
                "overallUsage": {
                    "values": [
                        {
                            "timestamp": "1970-01-01T00:00:00",
                            "value": "zero",
                        },
                    ],
                },
                "swapUsageOverall": {
                    "values": [
                        {
                            "timestamp": "1970-01-01T00:00:00",
                            "value": "zero",
                        },
                    ],
                },
                "start": None,
                "step": 60,
            },
        },
    }


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
@pytest.mark.parametrize("mock_send_query", [["device", 2]], indirect=True)
def test_graphql_get_memory_usage_with_options(
    client,
    authorized_client,
    mock_send_query,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": MEMORY_USAGE_QUERY_WITH_OPTIONS,
            "variables": {
                "start": datetime.fromtimestamp(1720136108).isoformat(),
                "end": datetime.fromtimestamp(1720137319).isoformat(),
                "step": 90,
            },
        },
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "memoryUsage": {
                "averageUsageByService": {
                    "metrics": [
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_0.slice",
                                },
                            ],
                        },
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_1.slice",
                                },
                            ],
                        },
                    ],
                },
                "end": "2024-07-04T23:55:19",
                "maxUsageByService": {
                    "metrics": [
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_0.slice",
                                },
                            ],
                        },
                        {
                            "metricId": "unknown",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "/slice_name_1.slice",
                                },
                            ],
                        },
                    ],
                },
                "overallUsage": {
                    "values": [
                        {
                            "timestamp": "1970-01-01T00:00:00",
                            "value": "zero",
                        },
                    ],
                },
                "swapUsageOverall": {
                    "values": [
                        {
                            "timestamp": "1970-01-01T00:00:00",
                            "value": "zero",
                        },
                    ],
                },
                "start": "2024-07-04T23:35:08",
                "step": 90,
            },
        },
    }


def test_graphql_get_memory_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": MEMORY_USAGE_QUERY},
    )
    assert_empty(response)


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
def test_graphql_get_cpu_usage(
    client,
    authorized_client,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={"query": CPU_USAGE_QUERY},
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "cpuUsage": {
                "end": None,
                "overallUsage": {
                    "values": [
                        {
                            "timestamp": "1970-01-01T00:00:00",
                            "value": "zero",
                        },
                    ],
                },
                "start": None,
                "step": 60,
            },
        },
    }


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
def test_graphql_get_cpu_usage_with_options(
    client,
    authorized_client,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": CPU_USAGE_QUERY_WITH_OPTIONS,
            "variables": {
                "start": datetime.fromtimestamp(1720136108).isoformat(),
                "end": datetime.fromtimestamp(1720137319).isoformat(),
                "step": 90,
            },
        },
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "cpuUsage": {
                "end": "2024-07-04T23:55:19",
                "overallUsage": {
                    "values": [
                        {
                            "timestamp": "1970-01-01T00:00:00",
                            "value": "zero",
                        },
                    ],
                },
                "start": "2024-07-04T23:35:08",
                "step": 90,
            },
        },
    }


def test_graphql_get_cpu_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": CPU_USAGE_QUERY},
    )
    assert_empty(response)


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
def test_graphql_get_network_usage(
    client,
    authorized_client,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={"query": NETWORK_USAGE_QUERY},
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "networkUsage": {
                "end": None,
                "overallUsage": {
                    "metrics": [
                        {
                            "metricId": "/unknown.slice",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "zero",
                                },
                            ],
                        },
                        {
                            "metricId": "/unknown.slice",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "zero",
                                },
                            ],
                        },
                    ],
                },
                "start": None,
                "step": 60,
            },
        },
    }


@pytest.mark.parametrize("mock_send_range_query", [["device", 2]], indirect=True)
def test_graphql_get_network_usage_with_options(
    client,
    authorized_client,
    mock_send_range_query,
    mock_get_status_active,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": NETWORK_USAGE_QUERY_WITH_OPTIONS,
            "variables": {
                "start": datetime.fromtimestamp(1720136108).isoformat(),
                "end": datetime.fromtimestamp(1720137319).isoformat(),
                "step": 90,
            },
        },
    )

    data = get_data(response)
    assert data == {
        "monitoring": {
            "networkUsage": {
                "end": "2024-07-04T23:55:19",
                "overallUsage": {
                    "metrics": [
                        {
                            "metricId": "/unknown.slice",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "zero",
                                },
                            ],
                        },
                        {
                            "metricId": "/unknown.slice",
                            "values": [
                                {
                                    "timestamp": "1970-01-01T00:00:00",
                                    "value": "zero",
                                },
                            ],
                        },
                    ],
                },
                "start": "2024-07-04T23:35:08",
                "step": 90,
            },
        },
    }


def test_graphql_get_network_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": NETWORK_USAGE_QUERY},
    )
    assert_empty(response)
