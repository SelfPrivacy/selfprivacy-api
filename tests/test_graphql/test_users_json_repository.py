# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest

from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.utils import WriteUserData
from tests.common import (
    generate_users_query,
    read_json,
)
from tests.test_graphql.common import (
    assert_empty,
    assert_errorcode,
    assert_ok,
    get_data,
)

invalid_usernames = [
    "messagebus",
    "postfix",
    "polkituser",
    "dovecot2",
    "dovenull",
    "nginx",
    "postgres",
    "systemd-journal-gateway",
    "prosody",
    "systemd-network",
    "systemd-resolve",
    "systemd-timesync",
    "opendkim",
    "rspamd",
    "sshd",
    "selfprivacy-api",
    "restic",
    "redis",
    "pleroma",
    "ocserv",
    "nextcloud",
    "memcached",
    "knot-resolver",
    "gitea",
    "bitwarden_rs",
    "vaultwarden",
    "acme",
    "virtualMail",
    "nixbld1",
    "nixbld2",
    "nixbld29",
    "nobody",
]


##  FIXTURES  ###################################################


@pytest.fixture
def use_json_repository(mocker):
    mocker.patch(
        "selfprivacy_api.actions.users.ACTIVE_USERS_PROVIDER", JsonUserRepository
    )


@pytest.fixture
def no_users(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "no_users.json")
    assert read_json(datadir / "no_users.json")["users"] == []
    return datadir


@pytest.fixture
def one_user(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "one_user.json")
    assert read_json(datadir / "one_user.json")["users"] == [
        {
            "username": "user1",
            "hashedPassword": "HASHED_PASSWORD_1",
            "sshKeys": ["ssh-rsa KEY user1@pc"],
        }
    ]
    return datadir


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


@pytest.fixture
def undefined_settings(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "users" not in read_json(datadir / "undefined.json")
    return datadir


@pytest.fixture
def no_users_no_admin_nobody(undefined_settings):
    datadir = undefined_settings
    with WriteUserData() as data:
        del data["username"]
        del data["sshKeys"]
    return datadir


@pytest.fixture
def no_primary_user(mocker, datadir):
    mocker.patch(
        "selfprivacy_api.utils.USERDATA_FILE", new=datadir / "no_primary_user.json"
    )
    data = read_json(datadir / "no_primary_user.json")
    assert "username" not in data
    assert "hashedMasterPassword" not in data
    assert len(data["users"]) == 2
    return datadir


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():  # pylint: disable=no-method-argument
        return (b"NEW_HASHED", None)

    returncode = 0


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


##  TESTS  ######################################################

API_USERS_INFO = """
allUsers {
    username
    sshKeys
}
"""


def api_all_users(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    output = get_data(response)["users"]["allUsers"]
    return output


def test_graphql_get_users_unauthorized(
    client, some_users, mock_subprocess_popen, use_json_repository
):
    """Test wrong auth"""
    response = client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert_empty(response)


def test_graphql_get_some_users(
    authorized_client, some_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert len(response.json()["data"]["users"]["allUsers"]) == 4
    assert response.json()["data"]["users"]["allUsers"][0]["username"] == "user1"
    assert response.json()["data"]["users"]["allUsers"][0]["sshKeys"] == [
        "ssh-rsa KEY user1@pc"
    ]

    assert response.json()["data"]["users"]["allUsers"][1]["username"] == "user2"
    assert response.json()["data"]["users"]["allUsers"][1]["sshKeys"] == []

    assert response.json()["data"]["users"]["allUsers"][3]["username"] == "tester"
    assert response.json()["data"]["users"]["allUsers"][3]["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]


def test_graphql_get_no_users(
    authorized_client, no_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["allUsers"]) == 1
    assert response.json()["data"]["users"]["allUsers"][0]["username"] == "tester"
    assert response.json()["data"]["users"]["allUsers"][0]["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]


def test_graphql_get_users_undefined_but_admin(
    authorized_client, undefined_settings, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["allUsers"]) == 1
    assert response.json()["data"]["users"]["allUsers"][0]["username"] == "tester"
    assert response.json()["data"]["users"]["allUsers"][0]["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]


def test_graphql_get_users_undefined_no_admin(
    authorized_client, no_users_no_admin_nobody, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["allUsers"]) == 0


API_GET_USER = """
query TestUsers($username: String!) {
    users {
        getUser(username: $username) {
            sshKeys
            username
        }
    }
}
"""


def test_graphql_get_one_user_unauthorized(
    client, one_user, mock_subprocess_popen, use_json_repository
):
    response = client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "user1",
            },
        },
    )
    assert_empty(response)


def test_graphql_get_one_user(
    authorized_client, one_user, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "user1",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "user1"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == [
        "ssh-rsa KEY user1@pc"
    ]


def test_graphql_get_some_user_undefined(
    authorized_client, undefined_settings, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "user1",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["getUser"] is None


def test_graphql_get_some_user(
    authorized_client, some_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "user2",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "user2"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == []


def test_graphql_get_root_user(
    authorized_client, some_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "root",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "root"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == [
        "ssh-ed25519 KEY test@pc"
    ]


def test_graphql_get_main_user(
    authorized_client, one_user, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "tester",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "tester"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]


def test_graphql_get_nonexistent_user(
    authorized_client, one_user, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "tyler_durden",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["getUser"] is None


API_CREATE_USERS_MUTATION = """
mutation createUser($user: UserMutationInput!) {
    users {
        createUser(user: $user) {
            success
            message
            code
            user {
                username
                sshKeys
            }
        }
    }
}
"""


def api_add_user_json(authorized_client, user_json: dict):
    # lowlevel for deeper testing of edgecases
    return authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": user_json,
            },
        },
    )


def api_add_user(authorized_client, username, password):
    response = api_add_user_json(
        authorized_client, {"username": username, "password": password}
    )
    output = get_data(response)["users"]["createUser"]
    return output


def test_graphql_add_user_unauthorized(
    client, one_user, mock_subprocess_popen, use_json_repository
):
    response = api_add_user_json(client, {"username": "user2", "password": "12345678"})
    assert_empty(response)


def test_graphql_add_user(
    authorized_client, one_user, mock_subprocess_popen, use_json_repository
):
    output = api_add_user(authorized_client, "user2", password="12345678")
    assert_ok(output, code=201)

    assert output["user"]["username"] == "user2"
    assert output["user"]["sshKeys"] == []


def test_graphql_add_user_when_undefined_settings(
    authorized_client, undefined_settings, mock_subprocess_popen, use_json_repository
):
    output = api_add_user(authorized_client, "user2", password="12345678")
    assert_ok(output, code=201)

    assert output["user"]["username"] == "user2"
    assert output["user"]["sshKeys"] == []


users_witn_empty_fields = [
    {"username": "user2", "password": ""},
    {"username": "", "password": "12345678"},
    {"username": "", "password": ""},
]


@pytest.mark.parametrize("user_json", users_witn_empty_fields)
def test_graphql_add_with_empty_fields(
    authorized_client, one_user, user_json, use_json_repository
):
    response = api_add_user_json(authorized_client, user_json)
    output = get_data(response)["users"]["createUser"]

    assert_errorcode(output, 400)
    assert output["user"] is None


@pytest.mark.parametrize("username", invalid_usernames)
def test_graphql_add_system_username(
    authorized_client, one_user, mock_subprocess_popen, username, use_json_repository
):
    output = api_add_user(authorized_client, username, password="12345678")

    assert_errorcode(output, code=409)
    assert output["user"] is None


def test_graphql_add_existing_user(authorized_client, one_user, use_json_repository):
    output = api_add_user(authorized_client, "user1", password="12345678")

    assert_errorcode(output, code=409)


# Linked to branch nhnn/inex/allow-no-main-username-nixos-25.11
#
# def test_graphql_add_user_when_no_admin_defined(
#     authorized_client, no_users_no_admin_nobody, use_json_repository
# ):
#     output = api_add_user(authorized_client, "tester", password="12345678")
#     assert_errorcode(output, code=400)
#     assert output["user"] is None


def test_graphql_add_long_username(
    authorized_client, one_user, mock_subprocess_popen, use_json_repository
):
    output = api_add_user(authorized_client, "a" * 32, password="12345678")

    assert_errorcode(output, code=400)
    assert output["user"] is None


# TODO: maybe make a username generating function to make a more comprehensive invalid username test
@pytest.mark.parametrize(
    "username", ["", "1", "фыр", "user1@", "^-^", "№:%##$^&@$&^()_"]
)
def test_graphql_add_invalid_username(
    authorized_client, one_user, mock_subprocess_popen, username, use_json_repository
):
    output = api_add_user(authorized_client, username, password="12345678")

    assert_errorcode(output, code=400)
    assert output["user"] is None


API_DELETE_USER_MUTATION = """
mutation deleteUser($username: String!) {
    users {
        deleteUser(username: $username) {
            success
            message
            code
        }
    }
}
"""


def test_graphql_delete_user_unauthorized(
    client, some_users, mock_subprocess_popen, use_json_repository
):
    response = client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": "user1"},
        },
    )
    assert_empty(response)


def test_graphql_delete_user(
    authorized_client, some_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": "user1"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["deleteUser"]["code"] == 200
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is True

    new_users = api_all_users(authorized_client)
    assert len(new_users) == 3
    usernames = [user["username"] for user in new_users]
    assert set(usernames) == set(["user2", "user3", "tester"])


@pytest.mark.parametrize("username", ["", "def"])
def test_graphql_delete_nonexistent_users(
    authorized_client, some_users, mock_subprocess_popen, username, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": username},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["deleteUser"]["code"] == 404
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is False


@pytest.mark.parametrize("username", invalid_usernames)
def test_graphql_delete_system_users(
    authorized_client, some_users, mock_subprocess_popen, username, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": username},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert (
        response.json()["data"]["users"]["deleteUser"]["code"] == 404
        or response.json()["data"]["users"]["deleteUser"]["code"] == 400
    )
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is False


def test_graphql_delete_main_user(
    authorized_client, some_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": "tester"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["deleteUser"]["code"] == 400
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is False


API_UPDATE_USER_MUTATION = """
mutation updateUser($user: UserMutationInput!) {
    users {
        updateUser(user: $user) {
            success
            message
            code
            user {
                username
                sshKeys
            }
        }
    }
}
"""


def test_graphql_update_user_unauthorized(
    client, some_users, mock_subprocess_popen, use_json_repository
):
    response = client.post(
        "/graphql",
        json={
            "query": API_UPDATE_USER_MUTATION,
            "variables": {
                "user": {
                    "username": "user1",
                    "password": "12345678",
                },
            },
        },
    )
    assert_empty(response)


def test_graphql_update_user(
    authorized_client, some_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UPDATE_USER_MUTATION,
            "variables": {
                "user": {
                    "username": "user1",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["updateUser"]["code"] == 200
    assert response.json()["data"]["users"]["updateUser"]["message"] is not None
    assert response.json()["data"]["users"]["updateUser"]["success"] is True

    assert response.json()["data"]["users"]["updateUser"]["user"]["username"] == "user1"
    assert response.json()["data"]["users"]["updateUser"]["user"]["sshKeys"] == [
        "ssh-rsa KEY user1@pc"
    ]


def test_graphql_update_nonexistent_user(
    authorized_client, some_users, mock_subprocess_popen, use_json_repository
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UPDATE_USER_MUTATION,
            "variables": {
                "user": {
                    "username": "user666",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["updateUser"]["code"] == 200
    assert response.json()["data"]["users"]["updateUser"]["message"] is not None
    assert response.json()["data"]["users"]["updateUser"]["success"] is True

    assert response.json()["data"]["users"]["updateUser"]["user"] is None


def test_graphql_get_users_no_primary_user(
    authorized_client, no_primary_user, mock_subprocess_popen, use_json_repository
):
    """Test that API works correctly when username and hashedMasterPassword are missing"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    # Should return only regular users + root (no primary user)
    users = response.json()["data"]["users"]["allUsers"]
    assert len(users) == 2  # user1, user2

    usernames = [user["username"] for user in users]
    assert "user1" in usernames
    assert "user2" in usernames
    assert "tester" not in usernames  # primary user should not be present


def test_graphql_get_specific_user_no_primary_user(
    authorized_client, no_primary_user, mock_subprocess_popen, use_json_repository
):
    """Test getting a specific regular user when primary user fields are missing"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "user1",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    user = response.json()["data"]["users"]["getUser"]
    assert user is not None
    assert user["username"] == "user1"
    assert user["sshKeys"] == ["ssh-rsa KEY user1@pc"]


def test_graphql_get_root_user_no_primary_user(
    authorized_client, no_primary_user, mock_subprocess_popen, use_json_repository
):
    """Test that root user is still accessible when primary user fields are missing"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USER,
            "variables": {
                "username": "root",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    user = response.json()["data"]["users"]["getUser"]
    assert user is not None
    assert user["username"] == "root"
    assert user["sshKeys"] == ["ssh-ed25519 KEY test@pc"]


# Linked to branch nhnn/inex/allow-no-main-username-nixos-25.11
#
# def test_graphql_add_user_no_primary_user(
#     authorized_client, no_primary_user, mock_subprocess_popen, use_json_repository
# ):
#     """Test that creating a user fails gracefully when primary user is not defined"""
#     output = api_add_user(authorized_client, "user3", password="12345678")

#     # Should fail because admin is not configured
#     assert_errorcode(output, code=400)
#     assert output["user"] is None


def test_graphql_delete_user_no_primary_user(
    authorized_client, no_primary_user, mock_subprocess_popen, use_json_repository
):
    """Test that deleting a user still works when primary user fields are missing"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": "user1"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["deleteUser"]["code"] == 200
    assert response.json()["data"]["users"]["deleteUser"]["success"] is True

    # Verify user was deleted
    new_users = api_all_users(authorized_client)
    usernames = [user["username"] for user in new_users]
    assert "user1" not in usernames
    assert "user2" in usernames


def test_graphql_update_user_no_primary_user(
    authorized_client, no_primary_user, mock_subprocess_popen, use_json_repository
):
    """Test that updating a user still works when primary user fields are missing"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UPDATE_USER_MUTATION,
            "variables": {
                "user": {
                    "username": "user1",
                    "password": "newpassword123",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["updateUser"]["code"] == 200
    assert response.json()["data"]["users"]["updateUser"]["success"] is True
    assert response.json()["data"]["users"]["updateUser"]["user"]["username"] == "user1"
