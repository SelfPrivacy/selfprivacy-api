# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import datetime
import json
import pytest
from mnemonic import Mnemonic


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


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def test_get_tokens_info(authorized_client, tokens_file):
    response = authorized_client.get("/auth/tokens")
    assert response.status_code == 200
    assert response.json == [
        {"name": "test_token", "date": "2022-01-14 08:31:10.789314", "is_caller": True},
        {
            "name": "test_token2",
            "date": "2022-01-14 08:31:10.789314",
            "is_caller": False,
        },
    ]


def test_get_tokens_unauthorized(client, tokens_file):
    response = client.get("/auth/tokens")
    assert response.status_code == 401


def test_delete_token_unauthorized(client, tokens_file):
    response = client.delete("/auth/tokens")
    assert response.status_code == 401
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_delete_token(authorized_client, tokens_file):
    response = authorized_client.delete(
        "/auth/tokens", json={"token_name": "test_token2"}
    )
    assert response.status_code == 200
    assert read_json(tokens_file) == {
        "tokens": [
            {
                "token": "TEST_TOKEN",
                "name": "test_token",
                "date": "2022-01-14 08:31:10.789314",
            }
        ]
    }


def test_delete_self_token(authorized_client, tokens_file):
    response = authorized_client.delete(
        "/auth/tokens", json={"token_name": "test_token"}
    )
    assert response.status_code == 400
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_delete_nonexistent_token(authorized_client, tokens_file):
    response = authorized_client.delete(
        "/auth/tokens", json={"token_name": "test_token3"}
    )
    assert response.status_code == 404
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_refresh_token_unauthorized(client, tokens_file):
    response = client.post("/auth/tokens")
    assert response.status_code == 401
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_refresh_token(authorized_client, tokens_file):
    response = authorized_client.post("/auth/tokens")
    assert response.status_code == 200
    new_token = response.json["token"]
    assert read_json(tokens_file)["tokens"][0]["token"] == new_token


# new device


def test_get_new_device_auth_token_unauthorized(client, tokens_file):
    response = client.get("/auth/new_device")
    assert response.status_code == 401
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_get_new_device_auth_token(authorized_client, tokens_file):
    response = authorized_client.post("/auth/new_device")
    assert response.status_code == 200
    assert "token" in response.json
    token = Mnemonic(language="english").to_entropy(response.json["token"]).hex()
    assert read_json(tokens_file)["new_device"]["token"] == token


def test_get_and_delete_new_device_token(authorized_client, tokens_file):
    response = authorized_client.post("/auth/new_device")
    assert response.status_code == 200
    assert "token" in response.json
    token = Mnemonic(language="english").to_entropy(response.json["token"]).hex()
    assert read_json(tokens_file)["new_device"]["token"] == token
    response = authorized_client.delete(
        "/auth/new_device", json={"token": response.json["token"]}
    )
    assert response.status_code == 200
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_delete_token_unauthenticated(client, tokens_file):
    response = client.delete("/auth/new_device")
    assert response.status_code == 401
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_get_and_authorize_new_device(client, authorized_client, tokens_file):
    response = authorized_client.post("/auth/new_device")
    assert response.status_code == 200
    assert "token" in response.json
    token = Mnemonic(language="english").to_entropy(response.json["token"]).hex()
    assert read_json(tokens_file)["new_device"]["token"] == token
    response = client.post(
        "/auth/new_device/authorize",
        json={"token": response.json["token"], "device": "new_device"},
    )
    assert response.status_code == 200
    assert read_json(tokens_file)["tokens"][2]["token"] == response.json["token"]
    assert read_json(tokens_file)["tokens"][2]["name"] == "new_device"


def test_authorize_new_device_with_invalid_token(client, tokens_file):
    response = client.post(
        "/auth/new_device/authorize",
        json={"token": "invalid_token", "device": "new_device"},
    )
    assert response.status_code == 404
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_get_and_authorize_used_token(client, authorized_client, tokens_file):
    response = authorized_client.post("/auth/new_device")
    assert response.status_code == 200
    assert "token" in response.json
    token = Mnemonic(language="english").to_entropy(response.json["token"]).hex()
    assert read_json(tokens_file)["new_device"]["token"] == token
    response = client.post(
        "/auth/new_device/authorize",
        json={"token": response.json["token"], "device": "new_device"},
    )
    assert response.status_code == 200
    assert read_json(tokens_file)["tokens"][2]["token"] == response.json["token"]
    assert read_json(tokens_file)["tokens"][2]["name"] == "new_device"
    response = client.post(
        "/auth/new_device/authorize",
        json={"token": response.json["token"], "device": "new_device"},
    )
    assert response.status_code == 404


def test_get_and_authorize_token_after_12_minutes(
    client, authorized_client, tokens_file
):
    response = authorized_client.post("/auth/new_device")
    assert response.status_code == 200
    assert "token" in response.json
    token = Mnemonic(language="english").to_entropy(response.json["token"]).hex()
    assert read_json(tokens_file)["new_device"]["token"] == token

    file_data = read_json(tokens_file)
    file_data["new_device"]["expiration"] = str(
        datetime.datetime.now() - datetime.timedelta(minutes=13)
    )
    write_json(tokens_file, file_data)

    response = client.post(
        "/auth/new_device/authorize",
        json={"token": response.json["token"], "device": "new_device"},
    )
    assert response.status_code == 404


def test_authorize_without_token(client, tokens_file):
    response = client.post(
        "/auth/new_device/authorize",
        json={"device": "new_device"},
    )
    assert response.status_code == 400
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


# Recovery tokens
# GET /auth/recovery_token returns token status
#  - if token is valid, returns 200 and token status
#   - token status:
#     - exists (boolean)
#     - valid (boolean)
#     - date (string)
#     - expiration (string)
#     - uses_left (int)
#  - if token is invalid, returns 400 and empty body
# POST /auth/recovery_token generates a new token
#  has two optional parameters:
#   - expiration (string in datetime format)
#   - uses_left (int)
# POST /auth/recovery_token/use uses the token
# required arguments:
#   - token (string)
#   - device (string)
#  - if token is valid, returns 200 and token
#  - if token is invalid, returns 404
#  - if request is invalid, returns 400


def test_get_recovery_token_status_unauthorized(client, tokens_file):
    response = client.get("/auth/recovery_token")
    assert response.status_code == 401
    assert read_json(tokens_file) == TOKENS_FILE_CONTETS


def test_generate_recovery_token(authorized_client, client, tokens_file):
    # Generate token without expiration and uses_left
    response = authorized_client.post("/auth/recovery_token")
    assert response.status_code == 200
    assert "token" in response.json
    token = Mnemonic(language="english").to_entropy(response.json["token"]).hex()
    assert read_json(tokens_file)["recovery_token"]["token"] == token

    # Try to use the token
    recovery_response = client.post(
        "/auth/recovery_token/use",
        json={"token": response.json["token"], "device": "recovery_device"},
    )
    assert recovery_response.status_code == 200
    new_token = recovery_response.json["token"]
    assert read_json(tokens_file)["tokens"][2]["token"] == new_token
    assert read_json(tokens_file)["tokens"][2]["name"] == "recovery_device"

    # Try to use token again
    recovery_response = client.post(
        "/auth/recovery_token/use",
        json={"token": response.json["token"], "device": "recovery_device2"},
    )
    assert recovery_response.status_code == 200
    new_token = recovery_response.json["token"]
    assert read_json(tokens_file)["tokens"][3]["token"] == new_token
    assert read_json(tokens_file)["tokens"][3]["name"] == "recovery_device2"
