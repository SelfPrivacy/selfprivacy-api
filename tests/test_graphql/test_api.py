# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import pytest

from tests.common import generate_api_query
from tests.test_graphql.test_api_devices import API_DEVICES_QUERY
from tests.test_graphql.test_api_recovery import API_RECOVERY_QUERY
from tests.test_graphql.test_api_version import API_VERSION_QUERY

TOKENS_FILE_CONTETS = {
    "tokens": [
        {
            "token": "TEST_TOKEN",
            "name": "test_token",
            "date": "2022-01-14 08:31:10.789314",
        },
        {
            "token": "TEST_TOKEN2",
            "name": "test_token2",
            "date": "2022-01-14 08:31:10.789314",
        },
    ]
}


def test_graphql_get_entire_api_data(authorized_client, tokens_file):
    response = authorized_client.get(
        "/graphql",
        json={
            "query": generate_api_query(
                [API_VERSION_QUERY, API_DEVICES_QUERY, API_RECOVERY_QUERY]
            )
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert "version" in response.get_json()["data"]["api"]
    assert response.json["data"]["api"]["devices"] is not None
    assert len(response.json["data"]["api"]["devices"]) == 2
    assert (
        response.json["data"]["api"]["devices"][0]["creationDate"]
        == "2022-01-14T08:31:10.789314"
    )
    assert response.json["data"]["api"]["devices"][0]["isCaller"] is True
    assert response.json["data"]["api"]["devices"][0]["name"] == "test_token"
    assert (
        response.json["data"]["api"]["devices"][1]["creationDate"]
        == "2022-01-14T08:31:10.789314"
    )
    assert response.json["data"]["api"]["devices"][1]["isCaller"] is False
    assert response.json["data"]["api"]["devices"][1]["name"] == "test_token2"
    assert response.json["data"]["api"]["recoveryKey"] is not None
    assert response.json["data"]["api"]["recoveryKey"]["exists"] is False
    assert response.json["data"]["api"]["recoveryKey"]["valid"] is False
    assert response.json["data"]["api"]["recoveryKey"]["creationDate"] is None
    assert response.json["data"]["api"]["recoveryKey"]["expirationDate"] is None
    assert response.json["data"]["api"]["recoveryKey"]["usesLeft"] is None
