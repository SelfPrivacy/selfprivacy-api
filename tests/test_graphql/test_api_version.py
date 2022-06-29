# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

from tests.common import generate_api_query

API_VERSION_QUERY = "version"

def test_graphql_get_api_version(authorized_client):
    response = authorized_client.get(
        "/graphql",
        json={
            "query": generate_api_query([API_VERSION_QUERY])
        },
    )
    assert response.status_code == 200
    assert "version" in response.get_json()["data"]["api"]


def test_graphql_api_version_unauthorized(client):
    response = client.get(
        "/graphql",
        json={
            "query": generate_api_query([API_VERSION_QUERY])
        },
    )
    assert response.status_code == 200
    assert "version" in response.get_json()["data"]["api"]
