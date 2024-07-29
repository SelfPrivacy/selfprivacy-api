# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

# from dataclasses import dataclass
# from datetime import datetime
# from typing import List, Dict
# import pytest

# from tests.test_graphql.common import (
#     assert_empty,
#     get_data,
# )

# MOCK_VALUES = [
#     [1720135748, "3.75"],
#     [1720135808, "4.525000000139698"],
#     [1720135868, "4.541666666433841"],
#     [1720135928, "4.574999999798209"],
#     [1720135988, "4.579166666759804"],
#     [1720136048, "3.8791666664959195"],
#     [1720136108, "4.5458333333954215"],
#     [1720136168, "4.566666666651145"],
#     [1720136228, "4.791666666666671"],
#     [1720136288, "4.720833333364382"],
#     [1720136348, "3.9624999999068677"],
#     [1720136408, "4.6875"],
#     [1720136468, "4.404166666790843"],
#     [1720136528, "4.31666666680637"],
#     [1720136588, "4.358333333317816"],
#     [1720136648, "3.7083333334885538"],
#     [1720136708, "4.558333333116025"],
#     [1720136768, "4.729166666511446"],
#     [1720136828, "4.75416666672875"],
#     [1720136888, "4.624999999844775"],
#     [1720136948, "3.9041666667132375"],
# ]


# @dataclass
# class DumbResponse:
#     status_code: int
#     json_data: dict

#     def json(self):
#         return self.json_data


# def generate_prometheus_response(result_type: str, result: List[Dict]):
#     return DumbResponse(
#         status_code=200,
#         json_data={"data": {"resultType": result_type, "result": result}},
#     )


# MOCK_SINGLE_METRIC_PROMETHEUS_RESPONSE = generate_prometheus_response(
#     "matrix", [{"values": MOCK_VALUES}]
# )
# MOCK_MULTIPLE_METRIC_DEVICE_PROMETHEUS_RESPONSE = generate_prometheus_response(
#     "matrix",
#     [
#         {"metric": {"device": "a"}, "values": MOCK_VALUES},
#         {"metric": {"device": "b"}, "values": MOCK_VALUES},
#         {"metric": {"device": "c"}, "values": MOCK_VALUES},
#     ],
# )

# # def generate_mock_metrics(name: str):
# #     return {
# #         "data": {
# #             "monitoring": {
# #                 f"{name}": {
# #                     "resultType": "matrix",
# #                     "result": [
# #                         {
# #                             "metric": {"instance": "127.0.0.1:9002"},
# #                             "values": ,
# #                         }
# #                     ],
# #                 }
# #             }
# #         }
# #     }


# # MOCK_CPU_USAGE_RESPONSE = generate_mock_metrics("cpuUsage")
# # MOCK_DISK_USAGE_RESPONSE = generate_mock_metrics("diskUsage")
# # MOCK_MEMORY_USAGE_RESPONSE = generate_mock_metrics("memoryUsage")


# def generate_mock_query(name):
#     return f"""
#     query Query {{
#         monitoring {{
#             {name} {{ resultType, result }}
#         }}
#     }}
#     """


# def generate_mock_query_with_options(name):
#     return f"""
#     query Query($start: DateTime, $end: DateTime, $step: Int) {{
#         monitoring {{
#             {name}(start: $start, end: $end, step: $step) {{ resultType, result }}
#         }}
#     }}
#     """


# def prometheus_result_from_dict(dict):
#     # return MonitoringQueryResult(result_type=dict["resultType"], result=dict["result"])
#     return dict


# @pytest.fixture
# def mock_cpu_usage(mocker):
#     mock = mocker.patch(
#         "selfprivacy_api.utils.prometheus.PrometheusQueries._send_query",
#         return_value=MOCK_CPU_USAGE_RESPONSE["data"]["monitoring"]["cpuUsage"],
#     )
#     return mock


# @pytest.fixture
# def mock_memory_usage(mocker):
#     mock = mocker.patch(
#         "selfprivacy_api.utils.prometheus.PrometheusQueries._send_query",
#         return_value=prometheus_result_from_dict(
#             MOCK_MEMORY_USAGE_RESPONSE["data"]["monitoring"]["memoryUsage"]
#         ),
#     )
#     return mock


# @pytest.fixture
# def mock_disk_usage(mocker):
#     mock = mocker.patch(
#         "selfprivacy_api.utils.prometheus.PrometheusQueries._send_query",
#         return_value=prometheus_result_from_dict(
#             MOCK_DISK_USAGE_RESPONSE["data"]["monitoring"]["diskUsage"]
#         ),
#     )
#     return mock


# def test_graphql_get_disk_usage(client, authorized_client, mock_disk_usage):
#     response = authorized_client.post(
#         "/graphql",
#         json={"query": generate_mock_query("diskUsage")},
#     )

#     data = get_data(response)
#     assert data == MOCK_DISK_USAGE_RESPONSE["data"]


# def test_graphql_get_disk_usage_with_options(
#     client, authorized_client, mock_disk_usage
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={
#             "query": generate_mock_query_with_options("diskUsage"),
#             "variables": {
#                 "start": datetime.fromtimestamp(1720136108).isoformat(),
#                 "end": datetime.fromtimestamp(1720137319).isoformat(),
#                 "step": 90,
#             },
#         },
#     )

#     data = get_data(response)
#     assert data == MOCK_DISK_USAGE_RESPONSE["data"]


# def test_graphql_get_disk_usage_unauthorized(client):
#     response = client.post(
#         "/graphql",
#         json={"query": generate_mock_query("diskUsage")},
#     )
#     assert_empty(response)


# def test_graphql_get_memory_usage(client, authorized_client, mock_memory_usage):
#     response = authorized_client.post(
#         "/graphql",
#         json={"query": generate_mock_query("memoryUsage")},
#     )

#     data = get_data(response)
#     assert data == MOCK_MEMORY_USAGE_RESPONSE["data"]


# def test_graphql_get_memory_usage_with_options(
#     client, authorized_client, mock_memory_usage
# ):
#     response = authorized_client.post(
#         "/graphql",
#         json={
#             "query": generate_mock_query_with_options("memoryUsage"),
#             "variables": {
#                 "start": datetime.fromtimestamp(1720136108).isoformat(),
#                 "end": datetime.fromtimestamp(1720137319).isoformat(),
#                 "step": 90,
#             },
#         },
#     )

#     data = get_data(response)
#     assert data == MOCK_MEMORY_USAGE_RESPONSE["data"]


# def test_graphql_get_memory_usage_unauthorized(client):
#     response = client.post(
#         "/graphql",
#         json={"query": generate_mock_query("memoryUsage")},
#     )
#     assert_empty(response)


# def test_graphql_get_cpu_usage(client, authorized_client, mock_cpu_usage):
#     response = authorized_client.post(
#         "/graphql",
#         json={"query": generate_mock_query("cpuUsage")},
#     )

#     data = get_data(response)
#     assert data == MOCK_CPU_USAGE_RESPONSE["data"]


# def test_graphql_get_cpu_usage_with_options(client, authorized_client, mock_cpu_usage):
#     response = authorized_client.post(
#         "/graphql",
#         json={
#             "query": generate_mock_query_with_options("cpuUsage"),
#             "variables": {
#                 "start": datetime.fromtimestamp(1720136108).isoformat(),
#                 "end": datetime.fromtimestamp(1720137319).isoformat(),
#                 "step": 90,
#             },
#         },
#     )

#     data = get_data(response)
#     assert data == MOCK_CPU_USAGE_RESPONSE["data"]


# def test_graphql_get_cpu_usage_unauthorized(client):
#     response = client.post(
#         "/graphql",
#         json={"query": generate_mock_query("cpuUsage")},
#     )
#     assert_empty(response)
