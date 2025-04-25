import pytest

from tests.test_graphql.common import get_data, assert_ok, assert_empty


API_DELETE_EMAIL_PASSWORD_MUTATION = """
mutation deleteEmailPassword($username: String!, $uuid: String!) {
    emailPasswordMetadataMutations {
        deleteEmailPassword(username: $username, uuid: $uuid) {
            success
            message
            code
        }
    }
}
"""

API_GET_USER = """
query GetUser($username: String!) {
    users {
        getUser(username: $username) {
            username
            emailPasswordMetadata {
                uuid
                lastUsed
                expiresAt
                displayName
                createdAt
            }
        }
    }
}
"""

API_CREATE_USER = """
mutation CreateUser($username: String!, $password: String) {
  users {
    createUser(user: {username: $username, password: $password}) {
      code
      message
      success
      user {
        username
        emailPasswordMetadata {
          uuid
          expiresAt
          displayName
          createdAt
          lastUsed
        }
      }
    }
  }
}
"""


def api_delete_email_password(authorized_client, user: str, uuid: str):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_EMAIL_PASSWORD_MUTATION,
            "variables": {
                "username": user,
                "uuid": uuid,
            },
        },
    )
    data = get_data(response)
    result = data["emailPasswordMetadataMutations"]["deleteEmailPassword"]
    assert result is not None
    return result


def api_get_user(authorized_client, user: str):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": user,
            },
        },
    )
    data = get_data(response)
    result = data["users"]["getUser"]
    assert result is not None
    return result


def api_create_user(authorized_client, user: str, password: str):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USER,
            "variables": {
                "username": user,
                "password": password,
            },
        },
    )
    data = get_data(response)
    result = data["users"]["createUser"]
    assert result is not None
    return result


# ---


def test_graphql_api_delete_email_unauthorized(client):
    data = api_delete_email_password(client, user="test_user", uuid="uuuuid")
    assert_empty(data)


def test_graphql_api_create_user_unauthorized(client):
    data = api_create_user(client, user="test_user", password="uuuuwwu")
    assert_empty(data)


def test_add_email_password(authorized_client):
    username = "test_user"

    data = api_create_user(authorized_client, user=username, password="uuuuwwu")
    assert_ok(data)

    data = api_get_user(authorized_client, user=username)
    assert_ok(data)

    assert data["username"] == username
    assert data["emailPasswordMetadata"]["uuid"] is not None
    assert data["emailPasswordMetadata"]["displayName"] is None


# def test_delete_email_password_after_adding(authorized_client):
