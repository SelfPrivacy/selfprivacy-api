# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import pytest


@pytest.fixture
def domain_file(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.DOMAIN_FILE", datadir / "domain")
    return datadir


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():  # pylint: disable=no-method-argument
        return (b"", None)

    returncode = 0


class BrokenServiceMock(ProcessMock):
    """Mock subprocess.Popen for broken service"""

    def communicate():  # pylint: disable=no-method-argument
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
def mock_subprocess_check_output(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=b"Testing Linux"
    )
    return mock


API_REBUILD_SYSTEM_MUTATION = """
mutation rebuildSystem {
    runSystemRebuild {
        success
        message
        code
    }
}
"""


def test_graphql_system_rebuild_unauthorized(client, mock_subprocess_popen):
    """Test system rebuild without authorization"""
    response = client.post(
        "/graphql",
        json={
            "query": API_REBUILD_SYSTEM_MUTATION,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None
    assert mock_subprocess_popen.call_count == 0


def test_graphql_system_rebuild(authorized_client, mock_subprocess_popen):
    """Test system rebuild"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REBUILD_SYSTEM_MUTATION,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["runSystemRebuild"]["success"] is True
    assert response.json["data"]["runSystemRebuild"]["message"] is not None
    assert response.json["data"]["runSystemRebuild"]["code"] == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == [
        "systemctl",
        "start",
        "sp-nixos-rebuild.service",
    ]


API_UPGRADE_SYSTEM_MUTATION = """
mutation upgradeSystem {
    runSystemUpgrade {
        success
        message
        code
    }
}
"""


def test_graphql_system_upgrade_unauthorized(client, mock_subprocess_popen):
    """Test system upgrade without authorization"""
    response = client.post(
        "/graphql",
        json={
            "query": API_UPGRADE_SYSTEM_MUTATION,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None
    assert mock_subprocess_popen.call_count == 0


def test_graphql_system_upgrade(authorized_client, mock_subprocess_popen):
    """Test system upgrade"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UPGRADE_SYSTEM_MUTATION,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["runSystemUpgrade"]["success"] is True
    assert response.json["data"]["runSystemUpgrade"]["message"] is not None
    assert response.json["data"]["runSystemUpgrade"]["code"] == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == [
        "systemctl",
        "start",
        "sp-nixos-upgrade.service",
    ]


API_ROLLBACK_SYSTEM_MUTATION = """
mutation rollbackSystem {
    runSystemRollback {
        success
        message
        code
    }
}
"""


def test_graphql_system_rollback_unauthorized(client, mock_subprocess_popen):
    """Test system rollback without authorization"""
    response = client.post(
        "/graphql",
        json={
            "query": API_ROLLBACK_SYSTEM_MUTATION,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None
    assert mock_subprocess_popen.call_count == 0


def test_graphql_system_rollback(authorized_client, mock_subprocess_popen):
    """Test system rollback"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_ROLLBACK_SYSTEM_MUTATION,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["runSystemRollback"]["success"] is True
    assert response.json["data"]["runSystemRollback"]["message"] is not None
    assert response.json["data"]["runSystemRollback"]["code"] == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == [
        "systemctl",
        "start",
        "sp-nixos-rollback.service",
    ]


API_REBOOT_SYSTEM_MUTATION = """
mutation system {
    rebootSystem {
        success
        message
        code
    }
}
"""


def test_graphql_reboot_system_unauthorized(client, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_REBOOT_SYSTEM_MUTATION,
        },
    )

    assert response.status_code == 200
    assert response.json.get("data") is None

    assert mock_subprocess_popen.call_count == 0


def test_graphql_reboot_system(authorized_client, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REBOOT_SYSTEM_MUTATION,
        },
    )

    assert response.status_code == 200
    assert response.json.get("data") is not None

    assert response.json["data"]["rebootSystem"]["success"] is True
    assert response.json["data"]["rebootSystem"]["message"] is not None
    assert response.json["data"]["rebootSystem"]["code"] == 200

    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == ["reboot"]
