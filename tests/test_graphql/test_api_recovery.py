# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import pytest

from datetime import datetime, timezone

from tests.common import (
    generate_api_query,
    assert_recovery_recent,
    NearFuture,
    RECOVERY_KEY_VALIDATION_DATETIME,
)

# Graphql API's output should be timezone-naive
from tests.common import ten_hours_into_future_naive_utc as ten_hours_into_future
from tests.common import ten_hours_into_future as ten_hours_into_future_tz
from tests.common import ten_minutes_into_past_naive_utc as ten_hours_into_past

from tests.test_graphql.common import (
    assert_empty,
    get_data,
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
    data = get_data(response)

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
    output = get_data(response)["api"]["getNewRecoveryApiKey"]
    assert_ok(output)

    key = output["key"]
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
    output = get_data(response)["api"]["useRecoveryApiKey"]
    assert_ok(output)

    token = output["token"]
    assert token is not None
    assert_token_valid(client, token)
    set_client_token(client, token)
    assert device_name in [device["name"] for device in graphql_get_devices(client)]
    return token


def test_graphql_recovery_key_status_unauthorized(client):
    response = request_recovery_status(client)
    assert_empty(response)


def test_graphql_recovery_key_status_when_none_exists(authorized_client):
    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is False
    assert status["valid"] is False
    assert status["creationDate"] is None
    assert status["expirationDate"] is None
    assert status["usesLeft"] is None


API_RECOVERY_KEY_GENERATE_MUTATION = """
mutation TestGenerateRecoveryKey($limits: RecoveryKeyLimitsInput) {
    api {
        getNewRecoveryApiKey(limits: $limits) {
            success
            message
            code
            key
        }
    }
}
"""

API_RECOVERY_KEY_USE_MUTATION = """
mutation TestUseRecoveryKey($input: UseRecoveryKeyInput!) {
    api {
        useRecoveryApiKey(input: $input) {
            success
            message
            code
            token
        }
    }
}
"""


def test_graphql_generate_recovery_key(client, authorized_client):
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


@pytest.mark.parametrize(
    "expiration_date", [ten_hours_into_future(), ten_hours_into_future_tz()]
)
def test_graphql_generate_recovery_key_with_expiration_date(
    client, authorized_client, expiration_date: datetime
):
    key = graphql_make_new_recovery_key(authorized_client, expires_at=expiration_date)

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is True
    assert_recovery_recent(status["creationDate"])

    # timezone-aware comparison. Should pass regardless of server's tz
    assert datetime.fromisoformat(status["expirationDate"]) == expiration_date.replace(
        tzinfo=timezone.utc
    )

    assert status["usesLeft"] is None

    graphql_use_recovery_key(client, key, "new_test_token")
    # And again
    graphql_use_recovery_key(client, key, "new_test_token2")


def test_graphql_use_recovery_key_after_expiration(client, authorized_client, mocker):
    expiration_date = ten_hours_into_future()
    key = graphql_make_new_recovery_key(authorized_client, expires_at=expiration_date)

    # Timewarp to after it expires
    mock = mocker.patch(RECOVERY_KEY_VALIDATION_DATETIME, NearFuture)

    response = request_recovery_auth(client, key, "new_test_token3")
    output = get_data(response)["api"]["useRecoveryApiKey"]
    assert_errorcode(output, 404)

    assert output["token"] is None
    assert_original(authorized_client)

    status = graphql_recovery_status(authorized_client)
    assert status["exists"] is True
    assert status["valid"] is False
    assert_recovery_recent(status["creationDate"])

    # timezone-aware comparison. Should pass regardless of server's tz
    assert datetime.fromisoformat(status["expirationDate"]) == expiration_date.replace(
        tzinfo=timezone.utc
    )
    assert status["usesLeft"] is None


def test_graphql_generate_recovery_key_with_expiration_in_the_past(authorized_client):
    expiration_date = ten_hours_into_past()
    response = request_make_new_recovery_key(
        authorized_client, expires_at=expiration_date
    )

    output = get_data(response)["api"]["getNewRecoveryApiKey"]
    assert_errorcode(output, 400)

    assert output["key"] is None
    assert graphql_recovery_status(authorized_client)["exists"] is False


def test_graphql_generate_recovery_key_with_invalid_time_format(authorized_client):
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
    assert graphql_recovery_status(authorized_client)["exists"] is False


def test_graphql_generate_recovery_key_with_limited_uses(authorized_client, client):
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
    output = get_data(response)["api"]["useRecoveryApiKey"]
    assert_errorcode(output, 404)


def test_graphql_generate_recovery_key_with_negative_uses(authorized_client):
    response = request_make_new_recovery_key(authorized_client, uses=-1)

    output = get_data(response)["api"]["getNewRecoveryApiKey"]
    assert_errorcode(output, 400)
    assert output["key"] is None
    assert graphql_recovery_status(authorized_client)["exists"] is False


def test_graphql_generate_recovery_key_with_zero_uses(authorized_client):
    response = request_make_new_recovery_key(authorized_client, uses=0)

    output = get_data(response)["api"]["getNewRecoveryApiKey"]
    assert_errorcode(output, 400)
    assert output["key"] is None
    assert graphql_recovery_status(authorized_client)["exists"] is False
