# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
from tests.common import (
    DEVICE_KEY_VALIDATION_DATETIME,
    RECOVERY_KEY_VALIDATION_DATETIME,  # noqa: F401
    NearFuture,
    generate_api_query,  # noqa: F401
)
from tests.conftest import DEVICE_WE_AUTH_TESTS_WITH
from tests.test_graphql.common import (
    API_DEVICES_QUERY,  # noqa: F401
    ORIGINAL_DEVICES,
    assert_empty,
    assert_errorcode,
    assert_ok,
    assert_original,
    assert_same,
    assert_token_valid,
    get_data,
    graphql_get_devices,
    request_devices,
    set_client_token,
)


def graphql_get_caller_token_info(client):
    devices = graphql_get_devices(client)
    for device in devices:
        if device["isCaller"] is True:
            return device


def graphql_get_new_device_key(authorized_client) -> str:
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(get_data(response)["api"]["getNewDeviceApiKey"])

    key = response.json()["data"]["api"]["getNewDeviceApiKey"]["key"]
    assert key.split(" ").__len__() == 12
    return key


def graphql_try_auth_new_device(client, mnemonic_key, device_name):
    return client.post(
        "/graphql",
        json={
            "query": AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "input": {
                    "key": mnemonic_key,
                    "deviceName": device_name,
                }
            },
        },
    )


def graphql_authorize_new_device(client, mnemonic_key, device_name) -> str:
    response = graphql_try_auth_new_device(client, mnemonic_key, "new_device")
    assert_ok(get_data(response)["api"]["authorizeWithNewDeviceApiKey"])
    token = response.json()["data"]["api"]["authorizeWithNewDeviceApiKey"]["token"]
    assert_token_valid(client, token)
    return token


def test_graphql_tokens_info(authorized_client):
    assert_original(authorized_client)


def test_graphql_tokens_info_unauthorized(client):
    response = request_devices(client)
    assert_empty(response)


DELETE_TOKEN_MUTATION = """
mutation DeleteToken($device: String!) {
    api {
        deleteDeviceApiToken(device: $device) {
            success
            message
            code
        }
    }
}
"""


def test_graphql_delete_token_unauthorized(client):
    response = client.post(
        "/graphql",
        json={
            "query": DELETE_TOKEN_MUTATION,
            "variables": {
                "device": "test_token",
            },
        },
    )
    assert_empty(response)


def test_graphql_delete_token(authorized_client):
    test_devices = ORIGINAL_DEVICES.copy()
    device_to_delete = test_devices.pop(1)
    assert device_to_delete != DEVICE_WE_AUTH_TESTS_WITH

    response = authorized_client.post(
        "/graphql",
        json={
            "query": DELETE_TOKEN_MUTATION,
            "variables": {
                "device": device_to_delete["name"],
            },
        },
    )
    assert_ok(get_data(response)["api"]["deleteDeviceApiToken"])

    devices = graphql_get_devices(authorized_client)
    assert_same(devices, test_devices)


def test_graphql_delete_self_token(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": DELETE_TOKEN_MUTATION,
            "variables": {
                "device": DEVICE_WE_AUTH_TESTS_WITH["name"],
            },
        },
    )
    assert_errorcode(get_data(response)["api"]["deleteDeviceApiToken"], 400)
    assert_original(authorized_client)


def test_graphql_delete_nonexistent_token(
    authorized_client,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": DELETE_TOKEN_MUTATION,
            "variables": {
                "device": "test_token3",
            },
        },
    )
    assert_errorcode(get_data(response)["api"]["deleteDeviceApiToken"], 404)

    assert_original(authorized_client)


REFRESH_TOKEN_MUTATION = """
mutation RefreshToken {
    api {
        refreshDeviceApiToken {
            success
            message
            code
            token
        }
    }
}
"""


def test_graphql_refresh_token_unauthorized(client):
    response = client.post(
        "/graphql",
        json={"query": REFRESH_TOKEN_MUTATION},
    )
    assert_empty(response)


def test_graphql_refresh_token(authorized_client, client):
    caller_name_and_date = graphql_get_caller_token_info(authorized_client)
    response = authorized_client.post(
        "/graphql",
        json={"query": REFRESH_TOKEN_MUTATION},
    )
    assert_ok(get_data(response)["api"]["refreshDeviceApiToken"])

    new_token = response.json()["data"]["api"]["refreshDeviceApiToken"]["token"]
    assert_token_valid(client, new_token)

    set_client_token(client, new_token)
    assert graphql_get_caller_token_info(client) == caller_name_and_date


NEW_DEVICE_KEY_MUTATION = """
mutation NewDeviceKey {
    api {
        getNewDeviceApiKey {
            success
            message
            code
            key
        }
    }
}
"""


def test_graphql_get_new_device_auth_key_unauthorized(
    client,
):
    response = client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_empty(response)


INVALIDATE_NEW_DEVICE_KEY_MUTATION = """
mutation InvalidateNewDeviceKey {
    api {
        invalidateNewDeviceApiKey {
            success
            message
            code
        }
    }
}
"""


def test_graphql_invalidate_new_device_token_unauthorized(
    client,
):
    response = client.post(
        "/graphql",
        json={
            "query": INVALIDATE_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "device": "test_token",
            },
        },
    )
    assert_empty(response)


def test_graphql_get_and_delete_new_device_key(client, authorized_client):
    mnemonic_key = graphql_get_new_device_key(authorized_client)

    response = authorized_client.post(
        "/graphql",
        json={"query": INVALIDATE_NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(get_data(response)["api"]["invalidateNewDeviceApiKey"])

    response = graphql_try_auth_new_device(client, mnemonic_key, "new_device")
    assert_errorcode(get_data(response)["api"]["authorizeWithNewDeviceApiKey"], 404)


AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION = """
mutation AuthorizeWithNewDeviceKey($input: UseNewDeviceKeyInput!) {
    api {
        authorizeWithNewDeviceApiKey(input: $input) {
            success
            message
            code
            token
        }
    }
}
"""


def test_graphql_get_and_authorize_new_device(client, authorized_client):
    mnemonic_key = graphql_get_new_device_key(authorized_client)
    old_devices = graphql_get_devices(authorized_client)

    graphql_authorize_new_device(client, mnemonic_key, "new_device")
    new_devices = graphql_get_devices(authorized_client)

    assert len(new_devices) == len(old_devices) + 1
    assert "new_device" in [device["name"] for device in new_devices]


def test_graphql_authorize_new_device_with_invalid_key(client, authorized_client):
    response = graphql_try_auth_new_device(client, "invalid_token", "new_device")
    assert_errorcode(get_data(response)["api"]["authorizeWithNewDeviceApiKey"], 404)

    assert_original(authorized_client)


def test_graphql_get_and_authorize_used_key(client, authorized_client):
    mnemonic_key = graphql_get_new_device_key(authorized_client)

    graphql_authorize_new_device(client, mnemonic_key, "new_device")
    devices = graphql_get_devices(authorized_client)

    response = graphql_try_auth_new_device(client, mnemonic_key, "new_device2")
    assert_errorcode(get_data(response)["api"]["authorizeWithNewDeviceApiKey"], 404)

    assert graphql_get_devices(authorized_client) == devices


def test_graphql_get_and_authorize_key_after_12_minutes(
    client, authorized_client, mocker
):
    mnemonic_key = graphql_get_new_device_key(authorized_client)
    mock = mocker.patch(DEVICE_KEY_VALIDATION_DATETIME, NearFuture)

    response = graphql_try_auth_new_device(client, mnemonic_key, "new_device")
    assert_errorcode(get_data(response)["api"]["authorizeWithNewDeviceApiKey"], 404)


def test_graphql_authorize_without_token(
    client,
):
    response = client.post(
        "/graphql",
        json={
            "query": AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "input": {
                    "deviceName": "test_token",
                }
            },
        },
    )
    assert_empty(response)
