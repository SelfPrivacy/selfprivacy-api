# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import datetime
import pytest
from mnemonic import Mnemonic

from selfprivacy_api.repositories.tokens.json_tokens_repository import (
    JsonTokensRepository,
)
from selfprivacy_api.models.tokens.token import Token

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


@pytest.fixture
def token_repo():
    return JsonTokensRepository()


def graphql_get_devices(client):
    response = client.post(
        "/graphql",
        json={"query": generate_api_query([API_DEVICES_QUERY])},
    )
    data = assert_data(response)
    devices = data["api"]["devices"]
    assert devices is not None
    return devices


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
                "device": "test_token",
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


def test_graphql_refresh_token(authorized_client, tokens_file, token_repo):
    response = authorized_client.post(
        "/graphql",
        json={"query": REFRESH_TOKEN_MUTATION},
    )
    assert_ok(response, "refreshDeviceApiToken")

    token = token_repo.get_token_by_name("test_token")
    assert token == Token(
        token=response.json()["data"]["refreshDeviceApiToken"]["token"],
        device_name="test_token",
        created_at=datetime.datetime(2022, 1, 14, 8, 31, 10, 789314),
    )


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


def test_graphql_get_new_device_auth_key(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(response, "getNewDeviceApiKey")

    assert (
        response.json()["data"]["getNewDeviceApiKey"]["key"].split(" ").__len__() == 12
    )
    token = (
        Mnemonic(language="english")
        .to_entropy(response.json()["data"]["getNewDeviceApiKey"]["key"])
        .hex()
    )
    assert read_json(tokens_file)["new_device"]["token"] == token


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


def test_graphql_get_and_delete_new_device_key(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(response, "getNewDeviceApiKey")

    assert (
        response.json()["data"]["getNewDeviceApiKey"]["key"].split(" ").__len__() == 12
    )
    token = (
        Mnemonic(language="english")
        .to_entropy(response.json()["data"]["getNewDeviceApiKey"]["key"])
        .hex()
    )
    assert read_json(tokens_file)["new_device"]["token"] == token
    response = authorized_client.post(
        "/graphql",
        json={"query": INVALIDATE_NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(response, "invalidateNewDeviceApiKey")
    assert_original(authorized_client)


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
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(response, "getNewDeviceApiKey")

    mnemonic_key = response.json()["data"]["getNewDeviceApiKey"]["key"]
    assert mnemonic_key.split(" ").__len__() == 12
    key = Mnemonic(language="english").to_entropy(mnemonic_key).hex()
    assert read_json(tokens_file)["new_device"]["token"] == key

    response = client.post(
        "/graphql",
        json={
            "query": AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "input": {
                    "key": mnemonic_key,
                    "deviceName": "new_device",
                }
            },
        },
    )

    assert_ok(response, "authorizeWithNewDeviceApiKey")
    token = response.json()["data"]["authorizeWithNewDeviceApiKey"]["token"]
    assert read_json(tokens_file)["tokens"][2]["token"] == token
    assert read_json(tokens_file)["tokens"][2]["name"] == "new_device"


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
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert_ok(response, "getNewDeviceApiKey")
    mnemonic_key = response.json()["data"]["getNewDeviceApiKey"]["key"]
    assert mnemonic_key.split(" ").__len__() == 12
    key = Mnemonic(language="english").to_entropy(mnemonic_key).hex()
    assert read_json(tokens_file)["new_device"]["token"] == key

    response = client.post(
        "/graphql",
        json={
            "query": AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "input": {
                    "key": mnemonic_key,
                    "deviceName": "new_token",
                }
            },
        },
    )
    assert_ok(response, "authorizeWithNewDeviceApiKey")
    assert (
        read_json(tokens_file)["tokens"][2]["token"]
        == response.json()["data"]["authorizeWithNewDeviceApiKey"]["token"]
    )
    assert read_json(tokens_file)["tokens"][2]["name"] == "new_token"

    response = client.post(
        "/graphql",
        json={
            "query": AUTHORIZE_WITH_NEW_DEVICE_KEY_MUTATION,
            "variables": {
                "input": {
                    "key": mnemonic_key,
                    "deviceName": "test_token2",
                }
            },
        },
    )
    assert_errorcode(response, "authorizeWithNewDeviceApiKey", 404)
    assert read_json(tokens_file)["tokens"].__len__() == 3


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
