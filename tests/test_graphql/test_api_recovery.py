# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import datetime

from tests.common import (
    generate_api_query,
    mnemonic_to_hex,
    read_json,
    write_json,
    assert_recovery_recent,
)
from tests.test_graphql.common import assert_empty, assert_data, assert_ok

API_RECOVERY_QUERY = """
recoveryKey {
    exists
    valid
    creationDate
    expirationDate
    usesLeft
}
"""


def request_recovery_status(client):
    return client.post(
        "/graphql",
        json={"query": generate_api_query([API_RECOVERY_QUERY])},
    )


def graphql_recovery_status(client):
    response = request_recovery_status(client)
    data = assert_data(response)

    status = data["api"]["recoveryKey"]
    assert status is not None
    return status


def graphql_get_new_recovery_key(client):
    response = client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_GENERATE_MUTATION,
        },
    )
    assert_ok(response, "getNewRecoveryApiKey")
    key = response.json()["data"]["getNewRecoveryApiKey"]["key"]
    assert key is not None
    assert key.split(" ").__len__() == 18
    return key


def test_graphql_recovery_key_status_unauthorized(client, tokens_file):
    response = request_recovery_status(client)
    assert_empty(response)


def test_graphql_recovery_key_status_when_none_exists(authorized_client, tokens_file):
    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is False
    assert status["valid"] is False
    assert status["creationDate"] is None
    assert status["expirationDate"] is None
    assert status["usesLeft"] is None


API_RECOVERY_KEY_GENERATE_MUTATION = """
mutation TestGenerateRecoveryKey($limits: RecoveryKeyLimitsInput) {
    getNewRecoveryApiKey(limits: $limits) {
        success
        message
        code
        key
    }
}
"""

API_RECOVERY_KEY_USE_MUTATION = """
mutation TestUseRecoveryKey($input: UseRecoveryKeyInput!) {
    useRecoveryApiKey(input: $input) {
        success
        message
        code
        token
    }
}
"""


def test_graphql_generate_recovery_key(client, authorized_client, tokens_file):
    key = graphql_get_new_recovery_key(authorized_client)

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is True
    assert_recovery_recent(status["creationDate"])
    assert status["expirationDate"] is None
    assert status["usesLeft"] is None

    # Try to use token
    response = client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": key,
                    "deviceName": "new_test_token",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is not None
    assert (
        response.json()["data"]["useRecoveryApiKey"]["token"]
        == read_json(tokens_file)["tokens"][2]["token"]
    )
    assert read_json(tokens_file)["tokens"][2]["name"] == "new_test_token"

    # Try to use token again
    response = client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": key,
                    "deviceName": "new_test_token2",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is not None
    assert (
        response.json()["data"]["useRecoveryApiKey"]["token"]
        == read_json(tokens_file)["tokens"][3]["token"]
    )
    assert read_json(tokens_file)["tokens"][3]["name"] == "new_test_token2"


def test_graphql_generate_recovery_key_with_expiration_date(
    client, authorized_client, tokens_file
):
    expiration_date = datetime.datetime.now() + datetime.timedelta(minutes=5)
    expiration_date_str = expiration_date.strftime("%Y-%m-%dT%H:%M:%S.%f")
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_GENERATE_MUTATION,
            "variables": {
                "limits": {
                    "expirationDate": expiration_date_str,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["getNewRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is not None
    assert (
        response.json()["data"]["getNewRecoveryApiKey"]["key"].split(" ").__len__()
        == 18
    )
    assert read_json(tokens_file)["recovery_token"] is not None

    key = response.json()["data"]["getNewRecoveryApiKey"]["key"]
    assert read_json(tokens_file)["recovery_token"]["expiration"] == expiration_date_str
    assert read_json(tokens_file)["recovery_token"]["token"] == mnemonic_to_hex(key)

    time_generated = read_json(tokens_file)["recovery_token"]["date"]
    assert time_generated is not None
    assert (
        datetime.datetime.strptime(time_generated, "%Y-%m-%dT%H:%M:%S.%f")
        - datetime.timedelta(seconds=5)
        < datetime.datetime.now()
    )

    # Try to get token status
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_api_query([API_RECOVERY_QUERY])},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["api"]["recoveryKey"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["exists"] is True
    assert response.json()["data"]["api"]["recoveryKey"]["valid"] is True
    assert response.json()["data"]["api"]["recoveryKey"][
        "creationDate"
    ] == time_generated.replace("Z", "")
    assert (
        response.json()["data"]["api"]["recoveryKey"]["expirationDate"]
        == expiration_date_str
    )
    assert response.json()["data"]["api"]["recoveryKey"]["usesLeft"] is None

    # Try to use token
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": key,
                    "deviceName": "new_test_token",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is not None
    assert (
        response.json()["data"]["useRecoveryApiKey"]["token"]
        == read_json(tokens_file)["tokens"][2]["token"]
    )

    # Try to use token again
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": key,
                    "deviceName": "new_test_token2",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is not None
    assert (
        response.json()["data"]["useRecoveryApiKey"]["token"]
        == read_json(tokens_file)["tokens"][3]["token"]
    )

    # Try to use token after expiration date
    new_data = read_json(tokens_file)
    new_data["recovery_token"]["expiration"] = (
        datetime.datetime.now() - datetime.timedelta(minutes=5)
    ).strftime("%Y-%m-%dT%H:%M:%S.%f")
    write_json(tokens_file, new_data)
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": key,
                    "deviceName": "new_test_token3",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is False
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 404
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is None

    assert read_json(tokens_file)["tokens"] == new_data["tokens"]

    # Try to get token status
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_api_query([API_RECOVERY_QUERY])},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["api"]["recoveryKey"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["exists"] is True
    assert response.json()["data"]["api"]["recoveryKey"]["valid"] is False
    assert (
        response.json()["data"]["api"]["recoveryKey"]["creationDate"] == time_generated
    )
    assert (
        response.json()["data"]["api"]["recoveryKey"]["expirationDate"]
        == new_data["recovery_token"]["expiration"]
    )
    assert response.json()["data"]["api"]["recoveryKey"]["usesLeft"] is None


def test_graphql_generate_recovery_key_with_expiration_in_the_past(
    authorized_client, tokens_file
):
    expiration_date = datetime.datetime.now() - datetime.timedelta(minutes=5)
    expiration_date_str = expiration_date.strftime("%Y-%m-%dT%H:%M:%S.%f")

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_GENERATE_MUTATION,
            "variables": {
                "limits": {
                    "expirationDate": expiration_date_str,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["success"] is False
    assert response.json()["data"]["getNewRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["code"] == 400
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is None
    assert "recovery_token" not in read_json(tokens_file)


def test_graphql_generate_recovery_key_with_invalid_time_format(
    authorized_client, tokens_file
):
    expiration_date = "invalid_time_format"
    expiration_date_str = expiration_date

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_GENERATE_MUTATION,
            "variables": {
                "limits": {
                    "expirationDate": expiration_date_str,
                },
            },
        },
    )
    assert_empty(response)

    assert "recovery_token" not in read_json(tokens_file)


def test_graphql_generate_recovery_key_with_limited_uses(
    authorized_client, tokens_file
):

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_GENERATE_MUTATION,
            "variables": {
                "limits": {
                    "expirationDate": None,
                    "uses": 2,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["getNewRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is not None

    mnemonic_key = response.json()["data"]["getNewRecoveryApiKey"]["key"]
    key = mnemonic_to_hex(mnemonic_key)

    assert read_json(tokens_file)["recovery_token"]["token"] == key
    assert read_json(tokens_file)["recovery_token"]["uses_left"] == 2

    # Try to get token status
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_api_query([API_RECOVERY_QUERY])},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["api"]["recoveryKey"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["exists"] is True
    assert response.json()["data"]["api"]["recoveryKey"]["valid"] is True
    assert response.json()["data"]["api"]["recoveryKey"]["creationDate"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["expirationDate"] is None
    assert response.json()["data"]["api"]["recoveryKey"]["usesLeft"] == 2

    # Try to use token
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": mnemonic_key,
                    "deviceName": "test_token1",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is not None

    # Try to get token status
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_api_query([API_RECOVERY_QUERY])},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["api"]["recoveryKey"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["exists"] is True
    assert response.json()["data"]["api"]["recoveryKey"]["valid"] is True
    assert response.json()["data"]["api"]["recoveryKey"]["creationDate"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["expirationDate"] is None
    assert response.json()["data"]["api"]["recoveryKey"]["usesLeft"] == 1

    # Try to use token
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": mnemonic_key,
                    "deviceName": "test_token2",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is True
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 200
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is not None

    # Try to get token status
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_api_query([API_RECOVERY_QUERY])},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["api"]["recoveryKey"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["exists"] is True
    assert response.json()["data"]["api"]["recoveryKey"]["valid"] is False
    assert response.json()["data"]["api"]["recoveryKey"]["creationDate"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["expirationDate"] is None
    assert response.json()["data"]["api"]["recoveryKey"]["usesLeft"] == 0

    # Try to use token
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": mnemonic_key,
                    "deviceName": "test_token3",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["useRecoveryApiKey"]["success"] is False
    assert response.json()["data"]["useRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["useRecoveryApiKey"]["code"] == 404
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is None


def test_graphql_generate_recovery_key_with_negative_uses(
    authorized_client, tokens_file
):
    # Try to get token status
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_GENERATE_MUTATION,
            "variables": {
                "limits": {
                    "uses": -1,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["success"] is False
    assert response.json()["data"]["getNewRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["code"] == 400
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is None


def test_graphql_generate_recovery_key_with_zero_uses(authorized_client, tokens_file):
    # Try to get token status
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_GENERATE_MUTATION,
            "variables": {
                "limits": {
                    "uses": 0,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["success"] is False
    assert response.json()["data"]["getNewRecoveryApiKey"]["message"] is not None
    assert response.json()["data"]["getNewRecoveryApiKey"]["code"] == 400
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is None
