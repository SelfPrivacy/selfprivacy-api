# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import datetime
from mnemonic import Mnemonic


from tests.common import generate_api_query, read_json, write_json
from tests.conftest import DEVICE_WE_AUTH_TESTS_WITH, TOKENS_FILE_CONTENTS

ORIGINAL_DEVICES = TOKENS_FILE_CONTENTS["tokens"]

API_DEVICES_QUERY = """
devices {
    creationDate
    isCaller
    name
}
"""


def graphql_get_devices(client):
    response = client.post(
        "/graphql",
        json={"query": generate_api_query([API_DEVICES_QUERY])},
    )
    data = assert_data(response)
    devices = data["api"]["devices"]
    assert devices is not None
    return devices


def graphql_get_caller_token_info(client):
    devices = graphql_get_devices(client)
    for device in devices:
        if device["isCaller"] is True:
            return device


def assert_same(graphql_devices, abstract_devices):
    """Orderless comparison"""
    assert len(graphql_devices) == len(abstract_devices)
    for original_device in abstract_devices:
        assert original_device["name"] in [device["name"] for device in graphql_devices]
        for device in graphql_devices:
            if device["name"] == original_device["name"]:
                assert device["creationDate"] == original_device["date"].isoformat()


def assert_original(client):
    devices = graphql_get_devices(client)
    assert_same(devices, ORIGINAL_DEVICES)

    for device in devices:
        if device["name"] == DEVICE_WE_AUTH_TESTS_WITH["name"]:
            assert device["isCaller"] is True
        else:
            assert device["isCaller"] is False


def assert_ok(response, request):
    data = assert_data(response)
    data[request]["success"] is True
    data[request]["message"] is not None
    data[request]["code"] == 200


def assert_errorcode(response, request, code):
    data = assert_data(response)
    data[request]["success"] is False
    data[request]["message"] is not None
    data[request]["code"] == code


def assert_empty(response):
    assert response.status_code == 200
    assert response.json().get("data") is None


def assert_data(response):
    assert response.status_code == 200
    data = response.json().get("data")
    assert data is not None
    return data


def set_client_token(client, token):
    client.headers.update({"Authorization": "Bearer " + token})


def assert_token_valid(client, token):
    set_client_token(client, token)
    assert graphql_get_devices(client) is not None


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
    response = client.post(
        "/graphql",
        json={"query": generate_api_query([API_DEVICES_QUERY])},
    )
    assert_empty(response)


DELETE_TOKEN_MUTATION = """
mutation DeleteToken($device: String!) {
    deleteDeviceApiToken(device: $device) {
        success
        message
        code
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


def test_graphql_delete_nonexistent_token(authorized_client, tokens_file):
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
    refreshDeviceApiToken {
        success
        message
        code
        token
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
    getNewDeviceApiKey {
        success
        message
        code
        key
    }
}
"""


def test_graphql_get_new_device_auth_key_unauthorized(client, tokens_file):
    response = client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_empty(response)


INVALIDATE_NEW_DEVICE_KEY_MUTATION = """
mutation InvalidateNewDeviceKey {
    invalidateNewDeviceApiKey {
        success
        message
        code
    }
}
"""


def test_graphql_invalidate_new_device_token_unauthorized(client, tokens_file):
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
    authorizeWithNewDeviceApiKey(input: $input) {
        success
        message
        code
        token
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
    response = client.post(
        "/graphql",
        json={
            "query": AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "input": {
                    "key": "invalid_token",
                    "deviceName": "test_token",
                }
            },
        },
    )
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
    client, authorized_client, tokens_file
):
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(response, "getNewDeviceApiKey")
    assert (
        response.json()["data"]["getNewDeviceApiKey"]["key"].split(" ").__len__() == 12
    )
    key = (
        Mnemonic(language="english")
        .to_entropy(response.json()["data"]["getNewDeviceApiKey"]["key"])
        .hex()
    )
    assert read_json(tokens_file)["new_device"]["token"] == key

    file_data = read_json(tokens_file)
    file_data["new_device"]["expiration"] = str(
        datetime.datetime.now() - datetime.timedelta(minutes=13)
    )
    write_json(tokens_file, file_data)

    response = client.post(
        "/graphql",
        json={
            "query": AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "input": {
                    "key": key,
                    "deviceName": "test_token",
                }
            },
        },
    )
    assert_errorcode(response, "authorizeWithNewDeviceApiKey", 404)


def test_graphql_authorize_without_token(client, tokens_file):
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
