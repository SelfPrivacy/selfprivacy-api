import json
from os import read
import pytest


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


###############################################################################


@pytest.fixture
def ssh_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_off.json")
    assert read_json(datadir / "turned_off.json")["ssh"]["enable"] == False
    assert (
        read_json(datadir / "turned_off.json")["ssh"]["passwordAuthentication"] == True
    )
    return datadir


@pytest.fixture
def ssh_on(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_on.json")
    assert (
        read_json(datadir / "turned_off.json")["ssh"]["passwordAuthentication"] == True
    )
    assert read_json(datadir / "turned_on.json")["ssh"]["enable"] == True
    return datadir


@pytest.fixture
def all_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "all_off.json")
    assert read_json(datadir / "all_off.json")["ssh"]["passwordAuthentication"] == False
    assert read_json(datadir / "all_off.json")["ssh"]["enable"] == False
    return datadir


@pytest.fixture
def undefined_settings(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "ssh" not in read_json(datadir / "undefined.json")
    return datadir


@pytest.fixture
def root_and_admin_have_keys(mocker, datadir):
    mocker.patch(
        "selfprivacy_api.utils.USERDATA_FILE",
        new=datadir / "root_and_admin_have_keys.json",
    )
    assert read_json(datadir / "root_and_admin_have_keys.json")["ssh"]["enable"] == True
    assert (
        read_json(datadir / "root_and_admin_have_keys.json")["ssh"][
            "passwordAuthentication"
        ]
        == True
    )
    assert read_json(datadir / "root_and_admin_have_keys.json")["ssh"]["rootKeys"] == [
        "ssh-ed25519 KEY test@pc"
    ]
    assert read_json(datadir / "root_and_admin_have_keys.json")["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]
    return datadir


###############################################################################


@pytest.mark.parametrize(
    "endpoint", ["ssh", "ssh/enable", "ssh/key/send", "ssh/keys/user"]
)
def test_unauthorized(client, ssh_off, endpoint):
    response = client.post(f"/services/{endpoint}")
    assert response.status_code == 401


def test_legacy_enable(authorized_client, ssh_off):
    response = authorized_client.post(f"/services/ssh/enable")
    assert response.status_code == 200
    assert read_json(ssh_off / "turned_off.json") == read_json(
        ssh_off / "turned_on.json"
    )


def test_legacy_enable_when_enabled(authorized_client, ssh_on):
    response = authorized_client.post(f"/services/ssh/enable")
    assert response.status_code == 200
    assert read_json(ssh_on / "turned_on.json") == read_json(ssh_on / "turned_on.json")


def test_get_current_settings_ssh_off(authorized_client, ssh_off):
    response = authorized_client.get("/services/ssh")
    assert response.status_code == 200
    assert response.json == {"enable": False, "passwordAuthentication": True}


def test_get_current_settings_ssh_on(authorized_client, ssh_on):
    response = authorized_client.get("/services/ssh")
    assert response.status_code == 200
    assert response.json == {"enable": True, "passwordAuthentication": True}


def test_get_current_settings_all_off(authorized_client, all_off):
    response = authorized_client.get("/services/ssh")
    assert response.status_code == 200
    assert response.json == {"enable": False, "passwordAuthentication": False}


def test_get_current_settings_undefined(authorized_client, undefined_settings):
    response = authorized_client.get("/services/ssh")
    assert response.status_code == 200
    assert response.json == {"enable": True, "passwordAuthentication": True}


available_settings = [
    {"enable": True, "passwordAuthentication": True},
    {"enable": True, "passwordAuthentication": False},
    {"enable": False, "passwordAuthentication": True},
    {"enable": False, "passwordAuthentication": False},
    {"enable": True},
    {"enable": False},
    {"passwordAuthentication": True},
    {"passwordAuthentication": False},
]


@pytest.mark.parametrize("settings", available_settings)
def test_set_settings_ssh_off(authorized_client, ssh_off, settings):
    response = authorized_client.put(f"/services/ssh", json=settings)
    assert response.status_code == 200
    data = read_json(ssh_off / "turned_off.json")["ssh"]
    if "enable" in settings:
        assert data["enable"] == settings["enable"]
    if "passwordAuthentication" in settings:
        assert data["passwordAuthentication"] == settings["passwordAuthentication"]


@pytest.mark.parametrize("settings", available_settings)
def test_set_settings_ssh_on(authorized_client, ssh_on, settings):
    response = authorized_client.put(f"/services/ssh", json=settings)
    assert response.status_code == 200
    data = read_json(ssh_on / "turned_on.json")["ssh"]
    if "enable" in settings:
        assert data["enable"] == settings["enable"]
    if "passwordAuthentication" in settings:
        assert data["passwordAuthentication"] == settings["passwordAuthentication"]


@pytest.mark.parametrize("settings", available_settings)
def test_set_settings_all_off(authorized_client, all_off, settings):
    response = authorized_client.put(f"/services/ssh", json=settings)
    assert response.status_code == 200
    data = read_json(all_off / "all_off.json")["ssh"]
    if "enable" in settings:
        assert data["enable"] == settings["enable"]
    if "passwordAuthentication" in settings:
        assert data["passwordAuthentication"] == settings["passwordAuthentication"]


@pytest.mark.parametrize("settings", available_settings)
def test_set_settings_undefined(authorized_client, undefined_settings, settings):
    response = authorized_client.put(f"/services/ssh", json=settings)
    assert response.status_code == 200
    data = read_json(undefined_settings / "undefined.json")["ssh"]
    if "enable" in settings:
        assert data["enable"] == settings["enable"]
    if "passwordAuthentication" in settings:
        assert data["passwordAuthentication"] == settings["passwordAuthentication"]

def test_add_root_key(authorized_client, ssh_on):
    response = authorized_client.put(f"/services/ssh/key/send", json={"public_key": "ssh-rsa KEY test@pc"})
    assert response.status_code == 201
    assert read_json(ssh_on / "turned_on.json")["ssh"]["rootKeys"] == [
        "ssh-rsa KEY test@pc",
    ]

def test_add_root_key_one_more(authorized_client, root_and_admin_have_keys):
    response = authorized_client.put(f"/services/ssh/key/send", json={"public_key": "ssh-rsa KEY test@pc"})
    assert response.status_code == 201
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")["ssh"]["rootKeys"] == [
        "ssh-ed25519 KEY test@pc",
        "ssh-rsa KEY test@pc",
    ]

def test_add_existing_root_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.put(f"/services/ssh/key/send", json={"public_key": "ssh-ed25519 KEY test@pc"})
    assert response.status_code == 409
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")["ssh"]["rootKeys"] == [
        "ssh-ed25519 KEY test@pc",
    ]

def test_add_invalid_root_key(authorized_client, ssh_on):
    response = authorized_client.put(f"/services/ssh/key/send", json={"public_key": "INVALID KEY test@pc"})
    assert response.status_code == 400

def test_add_root_key_via_wrong_endpoint(authorized_client, ssh_on):
    response = authorized_client.post(f"/services/ssh/keys/root", json={"public_key": "ssh-rsa KEY test@pc"})
    assert response.status_code == 400

def test_get_root_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.get(f"/services/ssh/keys/root")
    assert response.status_code == 200
    assert response.json == ["ssh-ed25519 KEY test@pc"]

def test_get_root_key_when_none(authorized_client, ssh_on):
    response = authorized_client.get(f"/services/ssh/keys/root")
    assert response.status_code == 200
    assert response.json == []

def test_delete_root_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.delete(f"/services/ssh/keys/root", json={"public_key": "ssh-ed25519 KEY test@pc"})
    assert response.status_code == 200
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")["ssh"]["rootKeys"] == []

def test_delete_root_nonexistent_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.delete(f"/services/ssh/keys/root", json={"public_key": "ssh-rsa KEY test@pc"})
    assert response.status_code == 404
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")["ssh"]["rootKeys"] == [
        "ssh-ed25519 KEY test@pc",
    ]

def test_get_admin_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.get(f"/services/ssh/keys/tester")
    assert response.status_code == 200
    assert response.json == ["ssh-rsa KEY test@pc"]

def test_get_admin_key_when_none(authorized_client, ssh_on):
    response = authorized_client.get(f"/services/ssh/keys/tester")
    assert response.status_code == 200
    assert response.json == []

def test_delete_admin_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.delete(f"/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY test@pc"})
    assert response.status_code == 200
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")["sshKeys"] == []

def test_add_admin_key(authorized_client, ssh_on):
    response = authorized_client.post(f"/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY test@pc"})
    assert response.status_code == 201
    assert read_json(ssh_on / "turned_on.json")["sshKeys"] == [
        "ssh-rsa KEY test@pc",
    ]

def test_add_admin_key_one_more(authorized_client, root_and_admin_have_keys):
    response = authorized_client.post(f"/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY_2 test@pc"})
    assert response.status_code == 201
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")["sshKeys"] == [
        "ssh-rsa KEY test@pc",
        "ssh-rsa KEY_2 test@pc"
    ]

def test_add_existing_admin_key(authorized_client, root_and_admin_have_keys):
    response = authorized_client.post(f"/services/ssh/keys/tester", json={"public_key": "ssh-rsa KEY test@pc"})
    assert response.status_code == 409
    assert read_json(root_and_admin_have_keys / "root_and_admin_have_keys.json")["sshKeys"] == [
        "ssh-rsa KEY test@pc",
    ]