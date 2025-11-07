# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import pytest

from selfprivacy_api.jobs import JobStatus, Jobs
from tests.test_graphql.common import assert_empty, assert_ok, get_data

from tests.conftest import (
    API_REBUILD_SYSTEM_UNIT,
    API_UPGRADE_SYSTEM_UNIT,
    assert_rebuild_or_upgrade_was_made,
    prepare_nixos_rebuild_calls,
)


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():  # pylint: disable=no-method-argument
        return (b"", None)

    returncode = 0


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


@pytest.fixture
def mock_sleep_intervals(mocker):
    mock_start = mocker.patch("selfprivacy_api.jobs.upgrade_system.START_INTERVAL", 0)
    mock_run = mocker.patch("selfprivacy_api.jobs.upgrade_system.RUN_INTERVAL", 0)
    return (mock_start, mock_run)


API_REBUILD_SYSTEM_MUTATION = """
mutation rebuildSystem {
    system {
        runSystemRebuild {
            success
            message
            code
            job {
                uid
            }
        }
    }
}
"""

API_UPGRADE_SYSTEM_MUTATION = """
mutation upgradeSystem {
    system {
        runSystemUpgrade {
            success
            message
            code
            job {
                uid
            }
        }
    }
}
"""


@pytest.mark.parametrize("action", ["rebuild", "upgrade"])
def test_graphql_system_rebuild_unauthorized(client, fp, action):
    """Test system rebuild without authorization"""
    query = (
        API_REBUILD_SYSTEM_MUTATION
        if action == "rebuild"
        else API_UPGRADE_SYSTEM_MUTATION
    )

    response = client.post(
        "/graphql",
        json={
            "query": query,
        },
    )
    assert_empty(response)
    # assert fp.call_count([fp.any()]) == 0


@pytest.mark.parametrize("action", ["rebuild", "upgrade"])
def test_graphql_system_rebuild(authorized_client, fp, action, mock_sleep_intervals):
    """Test system rebuild"""
    query = (
        API_REBUILD_SYSTEM_MUTATION
        if action == "rebuild"
        else API_UPGRADE_SYSTEM_MUTATION
    )
    unit_name = (
        API_REBUILD_SYSTEM_UNIT if action == "rebuild" else API_UPGRADE_SYSTEM_UNIT
    )

    prepare_nixos_rebuild_calls(fp, unit_name)

    response = authorized_client.post(
        "/graphql",
        json={
            "query": query,
        },
    )
    data = get_data(response)["system"][f"runSystem{action.capitalize()}"]
    assert_ok(data)

    assert_rebuild_or_upgrade_was_made(fp, unit_name)

    job_id = response.json()["data"]["system"][f"runSystem{action.capitalize()}"][
        "job"
    ]["uid"]
    assert Jobs.get_job(job_id).status == JobStatus.FINISHED
    assert Jobs.get_job(job_id).type_id == f"system.nixos.{action}"


@pytest.mark.parametrize("action", ["rebuild", "upgrade"])
def test_graphql_system_rebuild_failed(
    authorized_client, fp, action, mock_sleep_intervals
):
    """Test system rebuild"""
    unit_name = f"sp-nixos-{action}.service"
    query = (
        API_REBUILD_SYSTEM_MUTATION
        if action == "rebuild"
        else API_UPGRADE_SYSTEM_MUTATION
    )

    # Start the unit
    fp.register(["systemctl", "start", unit_name])

    # Wait for it to start
    fp.register(["systemctl", "show", unit_name], stdout="ActiveState=inactive")
    fp.register(["systemctl", "show", unit_name], stdout="ActiveState=inactive")
    fp.register(["systemctl", "show", unit_name], stdout="ActiveState=active")

    # Check its exectution
    fp.register(["systemctl", "show", unit_name], stdout="ActiveState=active")
    fp.register(
        ["journalctl", "-u", unit_name, "-n", "1", "-o", "cat"],
        stdout="Starting rebuild...",
    )

    fp.register(["systemctl", "show", unit_name], stdout="ActiveState=active")
    fp.register(
        ["journalctl", "-u", unit_name, "-n", "1", "-o", "cat"], stdout="Rebuilding..."
    )

    fp.register(["systemctl", "show", unit_name], stdout="ActiveState=failed")

    fp.register(
        ["journalctl", "-u", unit_name, "-n", "10", "-o", "cat"], stdout="Some error"
    )

    response = authorized_client.post(
        "/graphql",
        json={
            "query": query,
        },
    )
    data = get_data(response)["system"][f"runSystem{action.capitalize()}"]
    assert_ok(data)

    # assert fp.call_count(["systemctl", "start", unit_name]) == 1
    # assert fp.call_count(["systemctl", "show", unit_name]) == 6

    job_id = response.json()["data"]["system"][f"runSystem{action.capitalize()}"][
        "job"
    ]["uid"]
    assert Jobs.get_job(job_id).status == JobStatus.ERROR
    assert Jobs.get_job(job_id).type_id == f"system.nixos.{action}"


API_ROLLBACK_SYSTEM_MUTATION = """
mutation rollbackSystem {
    system {
        runSystemRollback {
            success
            message
            code
        }
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
    assert response.json().get("data") is None
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
    assert response.json().get("data") is not None
    assert response.json()["data"]["system"]["runSystemRollback"]["success"] is True
    assert response.json()["data"]["system"]["runSystemRollback"]["message"] is not None
    assert response.json()["data"]["system"]["runSystemRollback"]["code"] == 200
    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == [
        "systemctl",
        "start",
        "sp-nixos-rollback.service",
    ]


API_REBOOT_SYSTEM_MUTATION = """
mutation system {
    system {
        rebootSystem {
            success
            message
            code
        }
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
    assert response.json().get("data") is None

    assert mock_subprocess_popen.call_count == 0



    #     assert response.status_code == 200
    #     assert response.json().get("data") is not None

    #     assert response.json()["data"]["system"]["rebootSystem"]["success"] is True
    #     assert response.json()["data"]["system"]["rebootSystem"]["message"] is not None
    assert response.json()["data"]["system"]["rebootSystem"]["code"] == 200

    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == ["reboot"]
