# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import json
import os
import pytest
from selfprivacy_api.utils import get_domain


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def domain_file(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.DOMAIN_FILE", datadir / "domain")
    return datadir


@pytest.fixture
def turned_on(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_on.json")
    assert read_json(datadir / "turned_on.json")["autoUpgrade"]["enable"] == True
    assert read_json(datadir / "turned_on.json")["autoUpgrade"]["allowReboot"] == True
    assert read_json(datadir / "turned_on.json")["timezone"] == "Europe/Moscow"
    return datadir


@pytest.fixture
def turned_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_off.json")
    assert read_json(datadir / "turned_off.json")["autoUpgrade"]["enable"] == False
    assert read_json(datadir / "turned_off.json")["autoUpgrade"]["allowReboot"] == False
    assert read_json(datadir / "turned_off.json")["timezone"] == "Europe/Moscow"
    return datadir


@pytest.fixture
def undefined_config(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "autoUpgrade" not in read_json(datadir / "undefined.json")
    assert "timezone" not in read_json(datadir / "undefined.json")
    return datadir


@pytest.fixture
def no_values(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "no_values.json")
    assert "enable" not in read_json(datadir / "no_values.json")["autoUpgrade"]
    assert "allowReboot" not in read_json(datadir / "no_values.json")["autoUpgrade"]
    return datadir


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():
        return (b"", None)

    returncode = 0


class BrokenServiceMock(ProcessMock):
    """Mock subprocess.Popen"""

    def communicate():
        return (b"Testing error", None)

    returncode = 3


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


@pytest.fixture
def mock_os_chdir(mocker):
    mock = mocker.patch("os.chdir", autospec=True)
    return mock


@pytest.fixture
def mock_broken_service(mocker):
    mock = mocker.patch(
        "subprocess.Popen", autospec=True, return_value=BrokenServiceMock
    )
    return mock


@pytest.fixture
def mock_subprocess_check_output(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=b"Testing Linux"
    )
    return mock


def test_system_rebuild_unauthorized(client, mock_subprocess_popen):
    response = client.get("/system/configuration/apply")
    assert response.status_code == 401
    assert mock_subprocess_popen.call_count == 0


def test_system_rebuild(authorized_client, mock_subprocess_popen):
    response = authorized_client.get("/system/configuration/apply")
    assert response.status_code == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == [
        "systemctl",
        "start",
        "sp-nixos-rebuild.service",
    ]


def test_system_upgrade_unauthorized(client, mock_subprocess_popen):
    response = client.get("/system/configuration/upgrade")
    assert response.status_code == 401
    assert mock_subprocess_popen.call_count == 0


def test_system_upgrade(authorized_client, mock_subprocess_popen):
    response = authorized_client.get("/system/configuration/upgrade")
    assert response.status_code == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == [
        "systemctl",
        "start",
        "sp-nixos-upgrade.service",
    ]


def test_system_rollback_unauthorized(client, mock_subprocess_popen):
    response = client.get("/system/configuration/rollback")
    assert response.status_code == 401
    assert mock_subprocess_popen.call_count == 0


def test_system_rollback(authorized_client, mock_subprocess_popen):
    response = authorized_client.get("/system/configuration/rollback")
    assert response.status_code == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == [
        "systemctl",
        "start",
        "sp-nixos-rollback.service",
    ]


def test_reboot_system_unauthorized(client, mock_subprocess_popen):
    response = client.get("/system/reboot")
    assert response.status_code == 401
    assert mock_subprocess_popen.call_count == 0


def test_reboot_system(authorized_client, mock_subprocess_popen):
    response = authorized_client.get("/system/reboot")
    assert response.status_code == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == ["reboot"]
