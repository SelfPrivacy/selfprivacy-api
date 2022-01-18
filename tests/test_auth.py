# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import json
import pytest

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
        {"name": "test_token", "date": "2022-01-14 08:31:10.789314"},
        {"name": "test_token2", "date": "2022-01-14 08:31:10.789314"},
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
