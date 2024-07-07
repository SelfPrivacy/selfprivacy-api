# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import pytest
from datetime import datetime, timezone

from tests.test_graphql.common import (
    assert_empty,
    get_data,
    assert_ok,
    assert_errorcode,
    assert_original,
)


MOCK_CPU_USAGE_RESPONSE = {
    "data": {
        "monitoring": {
            "cpu_usage": {
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


@pytest.fixture
def mock_post():
    with patch(
        "path.to.authorized_client.post", return_value=mock_response
    ) as mock_method:
        yield mock_method


MOCK_DISKS_USAGE_RESPONSE = {
    "data": {
        "monitoring": {
            "filesystem_usage": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "device": "/dev/sda1",
                            "fstype": "ext4",
                            "instance": "127.0.0.1:9002",
                            "job": "node-exporter",
                            "mountpoint": "/",
                        },
                        "values": [
                            [1720135748, "58.96622455596515"],
                            [1720135808, "58.96624522725708"],
                            [1720135868, "58.96628656984096"],
                            [1720135928, "58.96632791242483"],
                            [1720135988, "58.96634858371677"],
                            [1720136048, "58.96638992630064"],
                            [1720136108, "58.96641059759258"],
                            [1720136168, "58.966451940176455"],
                            [1720136228, "58.96649328276033"],
                            [1720136288, "58.96651395405226"],
                            [1720136348, "58.966555296636145"],
                            [1720136408, "58.966596639220015"],
                            [1720136468, "58.96661731051196"],
                            [1720136528, "58.96665865309583"],
                            [1720136588, "58.9666999956797"],
                            [1720136648, "58.96672066697164"],
                            [1720136708, "58.96676200955551"],
                            [1720136768, "58.966782680847444"],
                            [1720136828, "58.96682402343132"],
                            [1720136888, "58.9668653660152"],
                            [1720136948, "58.966886037307134"],
                        ],
                    }
                ],
            }
        }
    }
}

MOCK_MEMORY_USAGE_RESPONSE = {
    "data": {
        "monitoring": {
            "memory_usage": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "instance": "127.0.0.1:9002",
                            "job": "node-exporter",
                        },
                        "values": [
                            [1720135748, "36.7520332586628"],
                            [1720135808, "36.75183144638857"],
                            [1720135868, "36.744969829065"],
                            [1720135928, "36.74456620451656"],
                            [1720135988, "36.74436439224233"],
                            [1720136048, "36.74396076769389"],
                            [1720136108, "36.73689733809611"],
                            [1720136168, "36.73669552582189"],
                            [1720136228, "36.93507699138262"],
                            [1720136288, "36.941131359609294"],
                            [1720136348, "36.93104074589817"],
                            [1720136408, "36.936691489576404"],
                            [1720136468, "36.93003168452705"],
                            [1720136528, "36.91994107081593"],
                            [1720136588, "36.91307945349236"],
                            [1720136648, "36.90964864483058"],
                            [1720136708, "36.90238340295857"],
                            [1720136768, "36.89592541018345"],
                            [1720136828, "36.89148554015055"],
                            [1720136888, "36.88462392282699"],
                            [1720136948, "36.626102399547946"],
                        ],
                    }
                ],
            }
        }
    }
}


DISKS_USAGE = """
query DefShouldSleepEnough {
    monitoring { 
        disks_usage { 
        <ты не сделал как я просил вывод данных из Prometheus, по этому тут будет ошибка>
        } 
    }
}
"""

DISKS_USAGE_WITH_OPTIONS = """
query DefShouldSleepEnough($start: int, $end: int, $step: int) {
    monitoring { 
        disks_usage(start: $start, end: $end, step: $step) { 
        <ты не сделал как я просил вывод данных из Prometheus, по этому тут будет ошибка>
        } 
    }
}
"""


def test_graphql_get_disks_usage(client, authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={"query": DISKS_USAGE},
    )

    data = get_data(response)["monitoring"]["disks_usage"]
    assert_ok(data)


def test_graphql_get_disks_usage_with_options(client, authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": DISKS_USAGE_WITH_OPTIONS,
            "variables": {
                "start": 1720136108,
                "end": 1720137319,
                "step": 90,
            },
        },
    )

    data = get_data(response)["monitoring"]["disks_usage"]
    assert_ok(data)


def test_graphql_get_disks_usage_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": DISKS_USAGE},
    )
    assert_empty(response)
