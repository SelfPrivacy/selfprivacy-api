import pytest

from tests.test_graphql.common import get_data, assert_ok, assert_empty
from tests.common import read_json
from selfprivacy_api.repositories.users.test_user_repository import TestUserRepository
from selfprivacy_api.actions.email_passwords import delete_all_email_passwords_hashes


@pytest.fixture
def use_test_repository(mocker):
    if hasattr(TestUserRepository, "_USERS_DB"):
        TestUserRepository._USERS_DB = {}

    mocker.patch(
        "selfprivacy_api.actions.users.ACTIVE_USERS_PROVIDER", TestUserRepository
    )


@pytest.fixture
def some_users(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "some_users.json")
    assert read_json(datadir / "some_users.json")["users"] == [
        {
            "username": "user1",
            "hashedPassword": "HASHED_PASSWORD_1",
            "sshKeys": ["ssh-rsa KEY user1@pc"],
        },
        {"username": "user2", "hashedPassword": "HASHED_PASSWORD_2", "sshKeys": []},
        {"username": "user3", "hashedPassword": "HASHED_PASSWORD_3"},
    ]
    return datadir


# ---


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
    return response


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
    return response


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
    return response


# ---


def test_graphql_api_delete_email_unauthorized(client, use_test_repository, some_users):
    response = api_delete_email_password(client, user="test_user", uuid="uuuuid")
    assert_empty(response)


def test_graphql_api_create_user_unauthorized(client, use_test_repository, some_users):
    response = api_create_user(client, user="test_user", password="uuuuwwu")
    assert_empty(response)


def test_add_email_password(authorized_client, use_test_repository, some_users):
    username = "test_user"
    delete_all_email_passwords_hashes(username)

    response = api_create_user(authorized_client, user=username, password="uuuuwwu")
    data = get_data(response)["users"]["createUser"]
    assert_ok(output=data, code=201)

    # ---

    response = api_get_user(authorized_client, user=username)
    data = get_data(response)["users"]["getUser"]
    assert data is not None

    assert data["username"] == username
    assert len(data["emailPasswordMetadata"]) >= 1
    assert data["emailPasswordMetadata"][0]["uuid"] is not None


def test_delete_email_password_after_adding(
    authorized_client, use_test_repository, some_users
):
    username = "test_user"
    delete_all_email_passwords_hashes(username)

    # ---

    response = api_create_user(authorized_client, user=username, password="uuuuwwu")
    data = get_data(response)["users"]["createUser"]
    assert_ok(output=data, code=201)

    # ---

    response = api_get_user(authorized_client, username)
    data = get_data(response)["users"]["getUser"]
    assert data is not None
    uuid = data["emailPasswordMetadata"][0]["uuid"]
    assert uuid is not None

    # ---

    response = api_delete_email_password(
        authorized_client=authorized_client,
        user=username,
        uuid=uuid,
    )
    data = get_data(response)["emailPasswordMetadataMutations"]["deleteEmailPassword"]
    assert_ok(output=data)
    assert data is not None

    # ---

    response = api_get_user(authorized_client, username)
    data = get_data(response)["users"]["getUser"]
    assert data is not None
    assert data["emailPasswordMetadata"] == []
