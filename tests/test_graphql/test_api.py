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


def test_graphql_get_api_version(authorized_client):
    response = authorized_client.get(
        "/graphql",
        json={
            "query": """
                query {
                    api {
                        version
                    }
                }
            """
        },
    )
    assert response.status_code == 200
    assert "version" in response.get_json()["data"]["api"]


def test_graphql_api_version_unauthorized(client):
    response = client.get(
        "/graphql",
        json={
            "query": """
                query {
                    api {
                        version
                    }
                }
            """
        },
    )
    assert response.status_code == 200
    assert "version" in response.get_json()["data"]["api"]


def test_graphql_tokens_info(authorized_client, tokens_file):
    response = authorized_client.get(
        "/graphql",
        json={
            "query": """
                query {
                    api {
                        devices {
                            creationDate
                            isCaller
                            name
                        }
                    }
                }
            """
        },
    )
    assert response.status_code == 200
    assert response.json == {
        "data": {
            "api": {
                "devices": [
                    {
                        "creationDate": "2022-01-14T08:31:10.789314",
                        "isCaller": True,
                        "name": "test_token",
                    },
                    {
                        "creationDate": "2022-01-14T08:31:10.789314",
                        "isCaller": False,
                        "name": "test_token2",
                    },
                ]
            }
        }
    }


def test_graphql_tokens_info_unauthorized(client, tokens_file):
    response = client.get(
        "/graphql",
        json={
            "query": """
                query {
                    api {
                        devices {
                            creationDate
                            isCaller
                            name
                        }
                    }
                }
            """
        },
    )
    assert response.status_code == 200
    assert response.json["data"] is None
