# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import json
import pytest


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


##  FIXTURES  ###################################################


@pytest.fixture
def ssh_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_off.json")
    assert not read_json(datadir / "turned_off.json")["ssh"]["enable"]
    assert read_json(datadir / "turned_off.json")["ssh"]["passwordAuthentication"]
    return datadir


@pytest.fixture
def ssh_on(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_on.json")
    assert read_json(datadir / "turned_off.json")["ssh"]["passwordAuthentication"]
    assert read_json(datadir / "turned_on.json")["ssh"]["enable"]
    return datadir


@pytest.fixture
def all_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "all_off.json")
    assert not read_json(datadir / "all_off.json")["ssh"]["passwordAuthentication"]
    assert not read_json(datadir / "all_off.json")["ssh"]["enable"]
    return datadir


@pytest.fixture
def undefined_settings(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "ssh" not in read_json(datadir / "undefined.json")
    return datadir


@pytest.fixture
def undefined_values(mocker, datadir):
    mocker.patch(
        "selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined_values.json"
    )
    assert "ssh" in read_json(datadir / "undefined_values.json")
    assert "enable" not in read_json(datadir / "undefined_values.json")["ssh"]
    assert (
        "passwordAuthentication"
        not in read_json(datadir / "undefined_values.json")["ssh"]
    )
    return datadir


@pytest.fixture
def root_and_admin_have_keys(mocker, datadir):
    mocker.patch(
        "selfprivacy_api.utils.USERDATA_FILE",
        new=datadir / "root_and_admin_have_keys.json",
    )
    assert read_json(datadir / "root_and_admin_have_keys.json")["ssh"]["enable"]
    assert read_json(datadir / "root_and_admin_have_keys.json")["ssh"][
        "passwordAuthentication"
    ]
    assert read_json(datadir / "root_and_admin_have_keys.json")["ssh"]["rootKeys"] == [
        "ssh-ed25519 KEY test@pc"
    ]
    assert read_json(datadir / "root_and_admin_have_keys.json")["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]
    return datadir


@pytest.fixture
def some_users(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "some_users.json")
    assert "users" in read_json(datadir / "some_users.json")
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


## /ssh/keys/{user} ######################################################


def test_delete_admin_key_on_undefined(authorized_client, undefined_settings):
    response = authorized_client.delete(
        "/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY test@pc"}
    )
    assert response.status_code == 404
    assert "sshKeys" not in read_json(undefined_settings / "undefined.json")


def test_add_admin_key(authorized_client, ssh_on):
    response = authorized_client.post(
        "/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY test@pc"}
    )
    assert response.status_code == 201
    assert read_json(ssh_on / "turned_on.json")["sshKeys"] == [
        "ssh-rsa KEY test@pc",
    ]


def test_add_admin_key_one_more(authorized_client, root_and_admin_have_keys):
    response = authorized_client.post(
        "/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY_2 test@pc"}
    )
    assert response.status_code == 201
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")[
        "sshKeys"
    ] == ["ssh-rsa KEY test@pc", "ssh-rsa KEY_2 test@pc"]


def test_add_existing_admin_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.post(
        "/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY test@pc"}
    )
    assert response.status_code == 409
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")[
        "sshKeys"
    ] == [
        "ssh-rsa KEY test@pc",
    ]


def test_add_invalid_admin_key(authorized_client, ssh_on):
    response = authorized_client.post(
        "/services/ssh/keys/tester", json={"public_key": "INVALID KEY test@pc"}
    )
    assert response.status_code == 400


@pytest.mark.parametrize("user", [1, 2, 3])
def test_get_user_key(authorized_client, some_users, user):
    response = authorized_client.get(f"/services/ssh/keys/user{user}")
    assert response.status_code == 200
    if user == 1:
        assert response.json() == ["ssh-rsa KEY user1@pc"]
    else:
        assert response.json() == []


def test_get_keys_of_nonexistent_user(authorized_client, some_users):
    response = authorized_client.get("/services/ssh/keys/user4")
    assert response.status_code == 404


def test_get_keys_of_undefined_users(authorized_client, undefined_settings):
    response = authorized_client.get("/services/ssh/keys/user1")
    assert response.status_code == 404


@pytest.mark.parametrize("user", [1, 2, 3])
def test_add_user_key(authorized_client, some_users, user):
    response = authorized_client.post(
        f"/services/ssh/keys/user{user}", json={"public_key": "ssh-ed25519 KEY test@pc"}
    )
    assert response.status_code == 201
    if user == 1:
        assert read_json(some_users / "some_users.json")["users"][user - 1][
            "sshKeys"
        ] == [
            "ssh-rsa KEY user1@pc",
            "ssh-ed25519 KEY test@pc",
        ]
    else:
        assert read_json(some_users / "some_users.json")["users"][user - 1][
            "sshKeys"
        ] == ["ssh-ed25519 KEY test@pc"]


def test_add_existing_user_key(authorized_client, some_users):
    response = authorized_client.post(
        "/services/ssh/keys/user1", json={"public_key": "ssh-rsa KEY user1@pc"}
    )
    assert response.status_code == 409
    assert read_json(some_users / "some_users.json")["users"][0]["sshKeys"] == [
        "ssh-rsa KEY user1@pc",
    ]


def test_add_invalid_user_key(authorized_client, some_users):
    response = authorized_client.post(
        "/services/ssh/keys/user1", json={"public_key": "INVALID KEY user1@pc"}
    )
    assert response.status_code == 400


def test_delete_user_key(authorized_client, some_users):
    response = authorized_client.delete(
        "/services/ssh/keys/user1", json={"public_key": "ssh-rsa KEY user1@pc"}
    )
    assert response.status_code == 200
    assert read_json(some_users / "some_users.json")["users"][0]["sshKeys"] == []


@pytest.mark.parametrize("user", [2, 3])
def test_delete_nonexistent_user_key(authorized_client, some_users, user):
    response = authorized_client.delete(
        f"/services/ssh/keys/user{user}", json={"public_key": "ssh-rsa KEY user1@pc"}
    )
    assert response.status_code == 404
    if user == 2:
        assert (
            read_json(some_users / "some_users.json")["users"][user - 1]["sshKeys"]
            == []
        )
    if user == 3:
        "sshKeys" not in read_json(some_users / "some_users.json")["users"][user - 1]


def test_add_keys_of_nonexistent_user(authorized_client, some_users):
    response = authorized_client.post(
        "/services/ssh/keys/user4", json={"public_key": "ssh-rsa KEY user4@pc"}
    )
    assert response.status_code == 404


def test_add_key_on_undefined_users(authorized_client, undefined_settings):
    response = authorized_client.post(
        "/services/ssh/keys/user1", json={"public_key": "ssh-rsa KEY user4@pc"}
    )
    assert response.status_code == 404


def test_delete_keys_of_nonexistent_user(authorized_client, some_users):
    response = authorized_client.delete(
        "/services/ssh/keys/user4", json={"public_key": "ssh-rsa KEY user4@pc"}
    )
    assert response.status_code == 404


def test_delete_key_when_undefined_users(authorized_client, undefined_settings):
    response = authorized_client.delete(
        "/services/ssh/keys/user1", json={"public_key": "ssh-rsa KEY user1@pc"}
    )
    assert response.status_code == 404
