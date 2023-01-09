# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

from tests.common import generate_api_query
from tests.test_graphql.common import assert_original_devices
from tests.test_graphql.test_api_devices import API_DEVICES_QUERY
from tests.test_graphql.test_api_recovery import API_RECOVERY_QUERY
from tests.test_graphql.test_api_version import API_VERSION_QUERY


def test_graphql_get_entire_api_data(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_api_query(
                [API_VERSION_QUERY, API_DEVICES_QUERY, API_RECOVERY_QUERY]
            )
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert "version" in response.json()["data"]["api"]

    devices = response.json()["data"]["api"]["devices"]
    assert devices is not None
    assert_original_devices(devices)

    assert response.json()["data"]["api"]["recoveryKey"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["exists"] is False
    assert response.json()["data"]["api"]["recoveryKey"]["valid"] is False
    assert response.json()["data"]["api"]["recoveryKey"]["creationDate"] is None
    assert response.json()["data"]["api"]["recoveryKey"]["expirationDate"] is None
    assert response.json()["data"]["api"]["recoveryKey"]["usesLeft"] is None
