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
    NearFuture,
    RECOVERY_KEY_VALIDATION_DATETIME,
)
from tests.test_graphql.common import (
    assert_empty,
    assert_data,
    assert_ok,
    assert_errorcode,
    assert_token_valid,
    assert_original,
    graphql_get_devices,
    set_client_token,
)

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


def request_make_new_recovery_key(client, expires_at=None, uses=None):
    json = {"query": API_RECOVERY_KEY_GENERATE_MUTATION}
    limits = {}

    if expires_at is not None:
        limits["expirationDate"] = expires_at.isoformat()
    if uses is not None:
        limits["uses"] = uses

    if limits != {}:
        json["variables"] = {"limits": limits}

    response = client.post("/graphql", json=json)
    return response


def graphql_make_new_recovery_key(client, expires_at=None, uses=None):
    response = request_make_new_recovery_key(client, expires_at, uses)
    assert_ok(response, "getNewRecoveryApiKey")
    key = response.json()["data"]["getNewRecoveryApiKey"]["key"]
    assert key is not None
    assert key.split(" ").__len__() == 18
    return key


def request_recovery_auth(client, key, device_name):
    return client.post(
        "/graphql",
        json={
            "query": API_RECOVERY_KEY_USE_MUTATION,
            "variables": {
                "input": {
                    "key": key,
                    "deviceName": device_name,
                },
            },
        },
    )


def graphql_use_recovery_key(client, key, device_name):
    response = request_recovery_auth(client, key, device_name)
    assert_ok(response, "useRecoveryApiKey")
    token = response.json()["data"]["useRecoveryApiKey"]["token"]
    assert token is not None
    assert_token_valid(client, token)
    set_client_token(client, token)
    assert device_name in [device["name"] for device in graphql_get_devices(client)]
    return token


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
    key = graphql_make_new_recovery_key(authorized_client)

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is True
    assert_recovery_recent(status["creationDate"])
    assert status["expirationDate"] is None
    assert status["usesLeft"] is None

    graphql_use_recovery_key(client, key, "new_test_token")
    # And again
    graphql_use_recovery_key(client, key, "new_test_token2")


def test_graphql_generate_recovery_key_with_expiration_date(
    client, authorized_client, tokens_file
):
    expiration_date = datetime.datetime.now() + datetime.timedelta(minutes=5)
    key = graphql_make_new_recovery_key(authorized_client, expires_at=expiration_date)

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is True
    assert_recovery_recent(status["creationDate"])
    assert status["expirationDate"] == expiration_date.isoformat()
    assert status["usesLeft"] is None

    graphql_use_recovery_key(client, key, "new_test_token")
    # And again
    graphql_use_recovery_key(client, key, "new_test_token2")


def test_graphql_use_recovery_key_after_expiration(
    client, authorized_client, tokens_file, mocker
):
    expiration_date = datetime.datetime.now() + datetime.timedelta(minutes=5)
    key = graphql_make_new_recovery_key(authorized_client, expires_at=expiration_date)

    # Timewarp to after it expires
    mock = mocker.patch(RECOVERY_KEY_VALIDATION_DATETIME, NearFuture)

    response = request_recovery_auth(client, key, "new_test_token3")
    assert_errorcode(response, "useRecoveryApiKey", 404)
    assert response.json()["data"]["useRecoveryApiKey"]["token"] is None
    assert_original(authorized_client)

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is False
    assert_recovery_recent(status["creationDate"])
    assert status["expirationDate"] == expiration_date.isoformat()
    assert status["usesLeft"] is None


def test_graphql_generate_recovery_key_with_expiration_in_the_past(
    authorized_client, tokens_file
):
    expiration_date = datetime.datetime.now() - datetime.timedelta(minutes=5)
    response = request_make_new_recovery_key(
        authorized_client, expires_at=expiration_date
    )

    assert_errorcode(response, "getNewRecoveryApiKey", 400)
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is None


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
    authorized_client, client, tokens_file
):

    mnemonic_key = graphql_make_new_recovery_key(authorized_client, uses=2)

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is True
    assert status["creationDate"] is not None
    assert status["expirationDate"] is None
    assert status["usesLeft"] == 2

    graphql_use_recovery_key(client, mnemonic_key, "new_test_token1")

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is True
    assert status["creationDate"] is not None
    assert status["expirationDate"] is None
    assert status["usesLeft"] == 1

    graphql_use_recovery_key(client, mnemonic_key, "new_test_token2")

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is False
    assert status["creationDate"] is not None
    assert status["expirationDate"] is None
    assert status["usesLeft"] == 0

    response = request_recovery_auth(client, mnemonic_key, "new_test_token3")
    assert_errorcode(response, "useRecoveryApiKey", 404)


def test_graphql_generate_recovery_key_with_negative_uses(
    authorized_client, tokens_file
):
    response = request_make_new_recovery_key(authorized_client, uses=-1)

    assert_errorcode(response, "getNewRecoveryApiKey", 400)
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is None


def test_graphql_generate_recovery_key_with_zero_uses(authorized_client, tokens_file):
    response = request_make_new_recovery_key(authorized_client, uses=0)

    assert_errorcode(response, "getNewRecoveryApiKey", 400)
    assert response.json()["data"]["getNewRecoveryApiKey"]["key"] is None
