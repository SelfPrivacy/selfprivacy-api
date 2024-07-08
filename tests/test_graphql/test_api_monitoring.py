# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import pytest
from tests.test_graphql.common import (
    assert_empty,
    get_data,
    assert_ok,
)


def generate_mock_metrics(name: str):
    return {
        "data": {
            "monitoring": {
                f"{name}": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"instance": "127.0.0.1:9002"},
                            "values": [
                                [1720135748, "3.75"],
                                [1720135808, "4.525000000139698"],
                                [1720135868, "4.541666666433841"],
                                [1720135928, "4.574999999798209"],
                                [1720135988, "4.579166666759804"],
                                [1720136048, "3.8791666664959195"],
                                [1720136108, "4.5458333333954215"],
                                [1720136168, "4.566666666651145"],
                                [1720136228, "4.791666666666671"],
                                [1720136288, "4.720833333364382"],
                                [1720136348, "3.9624999999068677"],
                                [1720136408, "4.6875"],
                                [1720136468, "4.404166666790843"],
                                [1720136528, "4.31666666680637"],
                                [1720136588, "4.358333333317816"],
                                [1720136648, "3.7083333334885538"],
                                [1720136708, "4.558333333116025"],
                                [1720136768, "4.729166666511446"],
                                [1720136828, "4.75416666672875"],
                                [1720136888, "4.624999999844775"],
                                [1720136948, "3.9041666667132375"],
                            ],
                        }
                    ],
                }
            }
        }
    }


MOCK_CPU_USAGE_RESPONSE = generate_mock_metrics("cpu_usage")
MOCK_DISK_USAGE_RESPONSE = generate_mock_metrics("disk_usage")
MOCK_MEMORY_USAGE_RESPONSE = generate_mock_metrics("memory_usage")


def generate_mock_query(name):
    return f"""
    query Query {{
        monitoring {{
            {name}
        }}
    }}
    """


def generate_mock_query_with_options(name):
    return f"""
    query Query($start: int, $end: int, $step: int) {{
        monitoring {{
            {name}(start: $start, end: $end, step: $step)
        }}
    }}
    """


@pytest.fixture
def mock_cpu_usage(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.prometheus.PrometheusQueries._sent_query",
        return_value=MOCK_CPU_USAGE_RESPONSE["data"]["monitoring"]["cpu_usage"],
    )
    return mock


@pytest.fixture
def mock_memory_usage(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.prometheus.PrometheusQueries._sent_query",
        return_value=MOCK_MEMORY_USAGE_RESPONSE["data"]["monitoring"]["memory_usage"],
    )
    return mock


@pytest.fixture
def mock_disk_usage(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.prometheus.PrometheusQueries._sent_query",
        return_value=MOCK_DISK_USAGE_RESPONSE["data"]["monitoring"]["disk_usage"],
    )
    return mock


def test_graphql_get_disk_usage(client, authorized_client, mock_disk_usage):
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_mock_query("disk_usage")},
    )

    data = get_data(response)
    assert_ok(data)
    assert data["data"] == MOCK_DISK_USAGE_RESPONSE["data"]


def test_graphql_get_disk_usage_with_options(
    client, authorized_client, mock_disk_usage
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_mock_query_with_options("disk_usage"),
            "variables": {
                "start": 1720136108,
                "end": 1720137319,
                "step": 90,
            },
        },
    )

    data = get_data(response)
    assert_ok(data)
    assert data["data"] == MOCK_DISK_USAGE_RESPONSE["data"]


def test_graphql_get_disk_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": generate_mock_query("disk_usage")},
    )
    assert_empty(response)


def test_graphql_get_memory_usage(client, authorized_client, mock_memory_usage):
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_mock_query("memory_usage")},
    )

    data = get_data(response)
    assert_ok(data)
    assert data["data"] == MOCK_MEMORY_USAGE_RESPONSE["data"]


def test_graphql_get_memory_usage_with_options(
    client, authorized_client, mock_memory_usage
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_mock_query_with_options("memory_usage"),
            "variables": {
                "start": 1720136108,
                "end": 1720137319,
                "step": 90,
            },
        },
    )

    data = get_data(response)
    assert_ok(data)
    assert data["data"] == MOCK_MEMORY_USAGE_RESPONSE["data"]


def test_graphql_get_memory_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": generate_mock_query("memory_usage")},
    )
    assert_empty(response)


def test_graphql_get_cpu_usage(client, authorized_client, mock_cpu_usage):
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_mock_query("cpu_usage")},
    )

    data = get_data(response)
    assert_ok(data)
    assert data["data"] == MOCK_CPU_USAGE_RESPONSE["data"]


def test_graphql_get_cpu_usage_with_options(client, authorized_client, mock_cpu_usage):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_mock_query_with_options("cpu_usage"),
            "variables": {
                "start": 1720136108,
                "end": 1720137319,
                "step": 90,
            },
        },
    )

    data = get_data(response)
    assert_ok(data)
    assert data["data"] == MOCK_CPU_USAGE_RESPONSE["data"]


def test_graphql_get_cpu_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": generate_mock_query("cpu_usage")},
    )
    assert_empty(response)
