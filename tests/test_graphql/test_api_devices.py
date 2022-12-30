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


def test_graphql_tokens_info(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_api_query([API_DEVICES_QUERY])},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["api"]["devices"] is not None
    assert len(response.json()["data"]["api"]["devices"]) == 2
    assert (
        response.json()["data"]["api"]["devices"][0]["creationDate"]
        == "2022-01-14T08:31:10.789314"
    )
    assert response.json()["data"]["api"]["devices"][0]["isCaller"] is True
    assert response.json()["data"]["api"]["devices"][0]["name"] == "test_token"
    assert (
        response.json()["data"]["api"]["devices"][1]["creationDate"]
        == "2022-01-14T08:31:10.789314"
    )
    assert response.json()["data"]["api"]["devices"][1]["isCaller"] is False
    assert response.json()["data"]["api"]["devices"][1]["name"] == "test_token2"


def test_graphql_tokens_info_unauthorized(client, tokens_file):
    response = client.post(
        "/graphql",
        json={"query": generate_api_query([API_DEVICES_QUERY])},
    )
    assert response.status_code == 200
    assert response.json()["data"] is None


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
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_graphql_delete_token(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": DELETE_TOKEN_MUTATION,
            "variables": {
                "device": "test_token2",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["deleteDeviceApiToken"]["success"] is True
    assert response.json()["data"]["deleteDeviceApiToken"]["message"] is not None
    assert response.json()["data"]["deleteDeviceApiToken"]["code"] == 200
    assert read_json(tokens_file) == {
        "tokens": [
            {
                "token": "TEST_TOKEN",
                "name": "test_token",
                "date": "2022-01-14 08:31:10.789314",
            }
        ]
    }


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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["deleteDeviceApiToken"]["success"] is False
    assert response.json()["data"]["deleteDeviceApiToken"]["message"] is not None
    assert response.json()["data"]["deleteDeviceApiToken"]["code"] == 400
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["deleteDeviceApiToken"]["success"] is False
    assert response.json()["data"]["deleteDeviceApiToken"]["message"] is not None
    assert response.json()["data"]["deleteDeviceApiToken"]["code"] == 404
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


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
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_graphql_refresh_token(authorized_client, tokens_file, token_repo):
    response = authorized_client.post(
        "/graphql",
        json={"query": REFRESH_TOKEN_MUTATION},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["refreshDeviceApiToken"]["success"] is True
    assert response.json()["data"]["refreshDeviceApiToken"]["message"] is not None
    assert response.json()["data"]["refreshDeviceApiToken"]["code"] == 200
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
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_graphql_get_new_device_auth_key(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["success"] is True
    assert response.json()["data"]["getNewDeviceApiKey"]["message"] is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["code"] == 200
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
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_graphql_get_and_delete_new_device_key(authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["success"] is True
    assert response.json()["data"]["getNewDeviceApiKey"]["message"] is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["code"] == 200
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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["invalidateNewDeviceApiKey"]["success"] is True
    assert response.json()["data"]["invalidateNewDeviceApiKey"]["message"] is not None
    assert response.json()["data"]["invalidateNewDeviceApiKey"]["code"] == 200
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["success"] is True
    assert response.json()["data"]["getNewDeviceApiKey"]["message"] is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["code"] == 200
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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["success"] is True
    assert (
        response.json()["data"]["authorizeWithNewDeviceApiKey"]["message"] is not None
    )
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["code"] == 200
    token = response.json()["data"]["authorizeWithNewDeviceApiKey"]["token"]
    assert read_json(tokens_file)["tokens"][2]["token"] == token
    assert read_json(tokens_file)["tokens"][2]["name"] == "new_device"


def test_graphql_authorize_new_device_with_invalid_key(client, tokens_file):
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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["success"] is False
    assert (
        response.json()["data"]["authorizeWithNewDeviceApiKey"]["message"] is not None
    )
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["code"] == 404
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_graphql_get_and_authorize_used_key(client, authorized_client, tokens_file):
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["success"] is True
    assert response.json()["data"]["getNewDeviceApiKey"]["message"] is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["code"] == 200
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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["success"] is True
    assert (
        response.json()["data"]["authorizeWithNewDeviceApiKey"]["message"] is not None
    )
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["code"] == 200
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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["success"] is False
    assert (
        response.json()["data"]["authorizeWithNewDeviceApiKey"]["message"] is not None
    )
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["code"] == 404
    assert read_json(tokens_file)["tokens"].__len__() == 3


def test_graphql_get_and_authorize_key_after_12_minutes(
    client, authorized_client, tokens_file
):
    response = authorized_client.post(
        "/graphql",
        json={"query": NEW_DEVICE_KEY_MUTATION},
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["success"] is True
    assert response.json()["data"]["getNewDeviceApiKey"]["message"] is not None
    assert response.json()["data"]["getNewDeviceApiKey"]["code"] == 200
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
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["success"] is False
    assert (
        response.json()["data"]["authorizeWithNewDeviceApiKey"]["message"] is not None
    )
    assert response.json()["data"]["authorizeWithNewDeviceApiKey"]["code"] == 404


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
    assert response.status_code == 200
    assert response.json().get("data") is None
