# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

# TODO(def): Finish this please.

# from datetime import datetime
# import pytest

# from selfprivacy_api.models.services import ServiceStatus

# from tests.test_graphql.common import (
#     assert_empty,
#     get_data,
# )


# @pytest.fixture
# def mock_get_status_active(mocker):
#     mock = mocker.patch(
#         "selfprivacy_api.graphql.queries.monitoring.Prometheus.get_status",
#         return_value=ServiceStatus.ACTIVE,
#     )
#     return mock


# @pytest.fixture
# def mock_send_query(mocker):
#     mock = mocker.patch(
#         "selfprivacy_api.utils.monitoring.MonitoringQueries._send_range_query",
#         # "selfprivacy_api.graphql.queries.monitoring._send_query",
#         return_value=["test result"],
#     )
#     return mock


# # ....


# CPU_USAGE_QUERY = """
# query {
#   monitoring {
#     cpuUsage {
#       start
#       end
#       step
#       overallUsage {
#         ... on MonitoringValues {
#           values {
#             timestamp
#             value
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#     }
#   }
# }
# """

# CPU_USAGE_QUERY_WITH_OPTIONS = """
# query Query($end: String!, $start: String!, $step: String!) {
#   monitoring {
#     cpuUsage(end: $end, start: $start, step: $step) {
#       end
#       overallUsage {
#         ... on MonitoringValues {
#           values {
#             timestamp
#             value
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       start
#       step
#     }
#   }
# }
# """

# MEMORY_USAGE_QUERY = """
# query Query {
#   monitoring {
#     memoryUsage {
#       averageUsageByService {
#         ... on MonitoringMetrics {
#           metrics {
#             metricId
#             values {
#               timestamp
#               value
#             }
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       end
#       maxUsageByService {
#         ... on MonitoringMetrics {
#           metrics {
#             metricId
#             values {
#               timestamp
#               value
#             }
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       overallUsage {
#         ... on MonitoringValues {
#           values {
#             timestamp
#             value
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       start
#       step
#     }
#   }
# }
# """

# MEMORY_USAGE_QUERY_WITH_OPTIONS = """
# query Query($end: String!, $start: String!, $step: String!) {
#   monitoring {
#     memoryUsage(end: $end, start: $start, step: $step) {
#       averageUsageByService {
#         ... on MonitoringMetrics {
#           metrics {
#             metricId
#             values {
#               timestamp
#               value
#             }
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       end
#       maxUsageByService {
#         ... on MonitoringMetrics {
#           metrics {
#             metricId
#             values {
#               timestamp
#               value
#             }
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       overallUsage {
#         ... on MonitoringValues {
#           values {
#             timestamp
#             value
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       start
#       step
#     }
#   }
# }
# """

# NETWORK_USAGE_QUERY = """
# query Query {
#   monitoring {
#     networkUsage {
#       end
#       start
#       step
#       overallUsage {
#         ... on MonitoringMetrics {
#           metrics {
#             metricId
#             values {
#               timestamp
#               value
#             }
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#     }
#   }
# }
# """

# NETWORK_USAGE_QUERY_WITH_OPTIONS = """
# query Query($end: String!, $start: String!, $step: String!) {
#   monitoring {
#     networkUsage(end: $end, start: $start, step: $step) {
#       end
#       overallUsage {
#         ... on MonitoringMetrics {
#           metrics {
#             metricId
#             values {
#               timestamp
#               value
#             }
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       start
#       step
#     }
#   }
# }
# """

# DISK_USAGE_QUERY = """
# query Query {
#   monitoring {
#     diskUsage {
#       __typename
#       start
#       end
#       step
#       overallUsage {
#         ... on MonitoringMetrics {
#             metrics {
#               metricId
#               values {
#                 timestamp
#                 value
#               }
#             }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#     }
#   }
# }
# """

# DISK_USAGE_QUERY_WITH_OPTIONS = """
# query Query($end: String!, $start: String!, $step: String!) {
#   monitoring {
#     diskUsage(end: $end, start: $start, step: $step) {
#       end
#       overallUsage {
#         ... on MonitoringMetrics {
#           metrics {
#             metricId
#             values {
#               timestamp
#               value
#             }
#           }
#         }
#         ... on MonitoringQueryError {
#           error
#         }
#       }
#       start
#       step
#     }
#   }
# }
# """


# def test_graphql_get_disk_usage(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={"query": DISK_USAGE_QUERY},
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_disk_usage_with_options(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={
#             "query": DISK_USAGE_QUERY,
#             "variables": {
#                 "start": datetime.fromtimestamp(1720136108).isoformat(),
#                 "end": datetime.fromtimestamp(1720137319).isoformat(),
#                 "step": 90,
#             },
#         },
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_disk_usage_unauthorized(client):
#     response = client.post(
#         "/graphql",
#         json={"query": DISK_USAGE_QUERY},
#     )
#     assert_empty(response)


# def test_graphql_get_memory_usage(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={"query": MEMORY_USAGE_QUERY},
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_memory_usage_with_options(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={
#             "query": MEMORY_USAGE_QUERY_WITH_OPTIONS,
#             "variables": {
#                 "start": datetime.fromtimestamp(1720136108).isoformat(),
#                 "end": datetime.fromtimestamp(1720137319).isoformat(),
#                 "step": 90,
#             },
#         },
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_memory_usage_unauthorized(client):
#     response = client.post(
#         "/graphql",
#         json={"query": MEMORY_USAGE_QUERY},
#     )
#     assert_empty(response)


# def test_graphql_get_cpu_usage(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={"query": CPU_USAGE_QUERY},
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_cpu_usage_with_options(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={
#             "query": CPU_USAGE_QUERY_WITH_OPTIONS,
#             "variables": {
#                 "start": datetime.fromtimestamp(1720136108).isoformat(),
#                 "end": datetime.fromtimestamp(1720137319).isoformat(),
#                 "step": 90,
#             },
#         },
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_cpu_usage_unauthorized(client):
#     response = client.post(
#         "/graphql",
#         json={"query": CPU_USAGE_QUERY},
#     )
#     assert_empty(response)


# def test_graphql_get_network_usage(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={"query": NETWORK_USAGE_QUERY},
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_network_usage_with_options(
#     client,
#     authorized_client,
#     mock_send_query,
#     mock_get_status_active,
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={
#             "query": NETWORK_USAGE_QUERY_WITH_OPTIONS,
#             "variables": {
#                 "start": datetime.fromtimestamp(1720136108).isoformat(),
#                 "end": datetime.fromtimestamp(1720137319).isoformat(),
#                 "step": 90,
#             },
#         },
#     )

#     data = get_data(response)
#     assert data == ["test result"]


# def test_graphql_get_network_usage_unauthorized(client):
#     response = client.post(
#         "/graphql",
#         json={"query": NETWORK_USAGE_QUERY},
#     )
#     assert_empty(response)
