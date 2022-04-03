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


def test_wrong_auth(wrong_auth_client):
    response = wrong_auth_client.get("/system/pythonVersion")
    assert response.status_code == 401


def test_get_domain(authorized_client, domain_file):
    assert get_domain() == "test-domain.tld"


## Timezones


def test_get_timezone_unauthorized(client, turned_on):
    response = client.get("/system/configuration/timezone")
    assert response.status_code == 401


def test_get_timezone(authorized_client, turned_on):
    response = authorized_client.get("/system/configuration/timezone")
    assert response.status_code == 200
    assert response.get_json() == "Europe/Moscow"


def test_get_timezone_on_undefined(authorized_client, undefined_config):
    response = authorized_client.get("/system/configuration/timezone")
    assert response.status_code == 200
    assert response.get_json() == "Europe/Uzhgorod"


def test_put_timezone_unauthorized(client, turned_on):
    response = client.put(
        "/system/configuration/timezone", json={"timezone": "Europe/Moscow"}
    )
    assert response.status_code == 401


def test_put_timezone(authorized_client, turned_on):
    response = authorized_client.put(
        "/system/configuration/timezone", json={"timezone": "Europe/Helsinki"}
    )
    assert response.status_code == 200
    assert read_json(turned_on / "turned_on.json")["timezone"] == "Europe/Helsinki"


def test_put_timezone_on_undefined(authorized_client, undefined_config):
    response = authorized_client.put(
        "/system/configuration/timezone", json={"timezone": "Europe/Helsinki"}
    )
    assert response.status_code == 200
    assert (
        read_json(undefined_config / "undefined.json")["timezone"] == "Europe/Helsinki"
    )


def test_put_timezone_without_timezone(authorized_client, turned_on):
    response = authorized_client.put("/system/configuration/timezone", json={})
    assert response.status_code == 400
    assert read_json(turned_on / "turned_on.json")["timezone"] == "Europe/Moscow"


def test_put_invalid_timezone(authorized_client, turned_on):
    response = authorized_client.put(
        "/system/configuration/timezone", json={"timezone": "Invalid/Timezone"}
    )
    assert response.status_code == 400
    assert read_json(turned_on / "turned_on.json")["timezone"] == "Europe/Moscow"


## AutoUpgrade


def test_get_auto_upgrade_unauthorized(client, turned_on):
    response = client.get("/system/configuration/autoUpgrade")
    assert response.status_code == 401


def test_get_auto_upgrade(authorized_client, turned_on):
    response = authorized_client.get("/system/configuration/autoUpgrade")
    assert response.status_code == 200
    assert response.get_json() == {
        "enable": True,
        "allowReboot": True,
    }


def test_get_auto_upgrade_on_undefined(authorized_client, undefined_config):
    response = authorized_client.get("/system/configuration/autoUpgrade")
    assert response.status_code == 200
    assert response.get_json() == {
        "enable": True,
        "allowReboot": False,
    }


def test_get_auto_upgrade_without_values(authorized_client, no_values):
    response = authorized_client.get("/system/configuration/autoUpgrade")
    assert response.status_code == 200
    assert response.get_json() == {
        "enable": True,
        "allowReboot": False,
    }


def test_get_auto_upgrade_turned_off(authorized_client, turned_off):
    response = authorized_client.get("/system/configuration/autoUpgrade")
    assert response.status_code == 200
    assert response.get_json() == {
        "enable": False,
        "allowReboot": False,
    }


def test_put_auto_upgrade_unauthorized(client, turned_on):
    response = client.put(
        "/system/configuration/autoUpgrade", json={"enable": True, "allowReboot": True}
    )
    assert response.status_code == 401


def test_put_auto_upgrade(authorized_client, turned_on):
    response = authorized_client.put(
        "/system/configuration/autoUpgrade", json={"enable": False, "allowReboot": True}
    )
    assert response.status_code == 200
    assert read_json(turned_on / "turned_on.json")["autoUpgrade"] == {
        "enable": False,
        "allowReboot": True,
    }


def test_put_auto_upgrade_on_undefined(authorized_client, undefined_config):
    response = authorized_client.put(
        "/system/configuration/autoUpgrade", json={"enable": False, "allowReboot": True}
    )
    assert response.status_code == 200
    assert read_json(undefined_config / "undefined.json")["autoUpgrade"] == {
        "enable": False,
        "allowReboot": True,
    }


def test_put_auto_upgrade_without_values(authorized_client, no_values):
    response = authorized_client.put(
        "/system/configuration/autoUpgrade", json={"enable": True, "allowReboot": True}
    )
    assert response.status_code == 200
    assert read_json(no_values / "no_values.json")["autoUpgrade"] == {
        "enable": True,
        "allowReboot": True,
    }


def test_put_auto_upgrade_turned_off(authorized_client, turned_off):
    response = authorized_client.put(
        "/system/configuration/autoUpgrade", json={"enable": True, "allowReboot": True}
    )
    assert response.status_code == 200
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"] == {
        "enable": True,
        "allowReboot": True,
    }


def test_put_auto_upgrade_without_enable(authorized_client, turned_off):
    response = authorized_client.put(
        "/system/configuration/autoUpgrade", json={"allowReboot": True}
    )
    assert response.status_code == 200
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"] == {
        "enable": False,
        "allowReboot": True,
    }


def test_put_auto_upgrade_without_allow_reboot(authorized_client, turned_off):
    response = authorized_client.put(
        "/system/configuration/autoUpgrade", json={"enable": True}
    )
    assert response.status_code == 200
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"] == {
        "enable": True,
        "allowReboot": False,
    }


def test_put_auto_upgrade_with_empty_json(authorized_client, turned_off):
    response = authorized_client.put("/system/configuration/autoUpgrade", json={})
    assert response.status_code == 200
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"] == {
        "enable": False,
        "allowReboot": False,
    }


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


def test_get_system_version_unauthorized(client, mock_subprocess_check_output):
    response = client.get("/system/version")
    assert response.status_code == 401
    assert mock_subprocess_check_output.call_count == 0


def test_get_system_version(authorized_client, mock_subprocess_check_output):
    response = authorized_client.get("/system/version")
    assert response.status_code == 200
    assert response.get_json() == {"system_version": "Testing Linux"}
    assert mock_subprocess_check_output.call_count == 1
    assert mock_subprocess_check_output.call_args[0][0] == ["uname", "-a"]


def test_reboot_system_unauthorized(client, mock_subprocess_popen):
    response = client.get("/system/reboot")
    assert response.status_code == 401
    assert mock_subprocess_popen.call_count == 0


def test_reboot_system(authorized_client, mock_subprocess_popen):
    response = authorized_client.get("/system/reboot")
    assert response.status_code == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == ["reboot"]


def test_get_python_version_unauthorized(client, mock_subprocess_check_output):
    response = client.get("/system/pythonVersion")
    assert response.status_code == 401
    assert mock_subprocess_check_output.call_count == 0


def test_get_python_version(authorized_client, mock_subprocess_check_output):
    response = authorized_client.get("/system/pythonVersion")
    assert response.status_code == 200
    assert response.get_json() == "Testing Linux"
    assert mock_subprocess_check_output.call_count == 1
    assert mock_subprocess_check_output.call_args[0][0] == ["python", "-V"]


def test_pull_system_unauthorized(client, mock_subprocess_popen):
    response = client.get("/system/configuration/pull")
    assert response.status_code == 401
    assert mock_subprocess_popen.call_count == 0


def test_pull_system(authorized_client, mock_subprocess_popen, mock_os_chdir):
    current_dir = os.getcwd()
    response = authorized_client.get("/system/configuration/pull")
    assert response.status_code == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == ["git", "pull"]
    assert mock_os_chdir.call_count == 2
    assert mock_os_chdir.call_args_list[0][0][0] == "/etc/nixos"
    assert mock_os_chdir.call_args_list[1][0][0] == current_dir


def test_pull_system_broken_repo(authorized_client, mock_broken_service, mock_os_chdir):
    current_dir = os.getcwd()
    response = authorized_client.get("/system/configuration/pull")
    assert response.status_code == 500
    assert mock_broken_service.call_count == 1
    assert mock_os_chdir.call_count == 2
    assert mock_os_chdir.call_args_list[0][0][0] == "/etc/nixos"
    assert mock_os_chdir.call_args_list[1][0][0] == current_dir
