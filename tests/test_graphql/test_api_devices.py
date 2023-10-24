# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
from tests.common import (
    RECOVERY_KEY_VALIDATION_DATETIME,
    DEVICE_KEY_VALIDATION_DATETIME,
    NearFuture,
    generate_api_query,
)
from tests.conftest import DEVICE_WE_AUTH_TESTS_WITH, TOKENS_FILE_CONTENTS
from tests.test_graphql.common import (
    assert_data,
    assert_empty,
    assert_ok,
    assert_errorcode,
    assert_token_valid,
    assert_original,
    assert_same,
    graphql_get_devices,
    request_devices,
    set_client_token,
    API_DEVICES_QUERY,
    ORIGINAL_DEVICES,
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
    assert_ok(response, "getNewDeviceApiKey")

    key = response.json()["data"]["getNewDeviceApiKey"]["key"]
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
    assert_ok(response, "authorizeWithNewDeviceApiKey")
    token = response.json()["data"]["authorizeWithNewDeviceApiKey"]["token"]
    assert_token_valid(client, token)


def test_graphql_tokens_info(authorized_client, tokens_file):
    assert_original(authorized_client)


def test_graphql_tokens_info_unauthorized(client, tokens_file):
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


def test_graphql_delete_token_unauthorized(client, tokens_file):
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


def test_graphql_delete_token(authorized_client, tokens_file):
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
    assert_ok(response, "deleteDeviceApiToken")

    devices = graphql_get_devices(authorized_client)
    assert_same(devices, test_devices)


def test_graphql_delete_self_token(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": DELETE_TOKEN_MUTATION,
            "variables": {
                "device": DEVICE_WE_AUTH_TESTS_WITH["name"],
            },
        },
    )
    assert_errorcode(response, "deleteDeviceApiToken", 400)
    assert_original(authorized_client)


def test_graphql_delete_nonexistent_token(
    authorized_client,
    tokens_file,
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
    assert_errorcode(response, "deleteDeviceApiToken", 404)

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


def test_graphql_refresh_token_unauthorized(client, tokens_file):
    response = client.post(
        "/graphql",
        json={"query": REFRESH_TOKEN_MUTATION},
    )
    assert_empty(response)


def test_graphql_refresh_token(authorized_client, client, tokens_file):
    caller_name_and_date = graphql_get_caller_token_info(authorized_client)
    response = authorized_client.post(
        "/graphql",
        json={"query": REFRESH_TOKEN_MUTATION},
    )
    assert_ok(response, "refreshDeviceApiToken")

    new_token = response.json()["data"]["refreshDeviceApiToken"]["token"]
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
    tokens_file,
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
    tokens_file,
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


def test_graphql_get_and_delete_new_device_key(client, authorized_client, tokens_file):
    mnemonic_key = graphql_get_new_device_key(authorized_client)

    response = authorized_client.post(
        "/graphql",
        json={"query": INVALIDATE_NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(response, "invalidateNewDeviceApiKey")

    response = graphql_try_auth_new_device(client, mnemonic_key, "new_device")
    assert_errorcode(response, "authorizeWithNewDeviceApiKey", 404)


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


def test_graphql_get_and_authorize_new_device(client, authorized_client, tokens_file):
    mnemonic_key = graphql_get_new_device_key(authorized_client)
    old_devices = graphql_get_devices(authorized_client)

    graphql_authorize_new_device(client, mnemonic_key, "new_device")
    new_devices = graphql_get_devices(authorized_client)

    assert len(new_devices) == len(old_devices) + 1
    assert "new_device" in [device["name"] for device in new_devices]


def test_graphql_authorize_new_device_with_invalid_key(
    client, authorized_client, tokens_file
):
    response = graphql_try_auth_new_device(client, "invalid_token", "new_device")
    assert_errorcode(response, "authorizeWithNewDeviceApiKey", 404)

    assert_original(authorized_client)


def test_graphql_get_and_authorize_used_key(client, authorized_client, tokens_file):
    mnemonic_key = graphql_get_new_device_key(authorized_client)

    graphql_authorize_new_device(client, mnemonic_key, "new_device")
    devices = graphql_get_devices(authorized_client)

    response = graphql_try_auth_new_device(client, mnemonic_key, "new_device2")
    assert_errorcode(response, "authorizeWithNewDeviceApiKey", 404)

    assert graphql_get_devices(authorized_client) == devices


def test_graphql_get_and_authorize_key_after_12_minutes(
    client, authorized_client, tokens_file, mocker
):
    mnemonic_key = graphql_get_new_device_key(authorized_client)
    mock = mocker.patch(DEVICE_KEY_VALIDATION_DATETIME, NearFuture)

    response = graphql_try_auth_new_device(client, mnemonic_key, "new_device")
    assert_errorcode(response, "authorizeWithNewDeviceApiKey", 404)


def test_graphql_authorize_without_token(
    client,
    tokens_file,
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
