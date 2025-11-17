# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import pytest

from selfprivacy_api.jobs import JobStatus, Jobs
from tests.test_graphql.common import assert_empty, assert_ok, get_data

from selfprivacy_api.services import ServiceStatus

from tests.conftest import (
    API_REBUILD_SYSTEM_UNIT,
    API_UPGRADE_SYSTEM_UNIT,
    mock_system_rebuild_flow
)


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
def test_graphql_system_rebuild_unauthorized(client, action):
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

@pytest.mark.parametrize("action", ["rebuild", "upgrade"])
def test_graphql_system_rebuild(authorized_client, mocker, action):
    """Test system rebuild"""
    query = (
        API_REBUILD_SYSTEM_MUTATION
        if action == "rebuild"
        else API_UPGRADE_SYSTEM_MUTATION
    )
    unit_name = (
        API_REBUILD_SYSTEM_UNIT if action == "rebuild" else API_UPGRADE_SYSTEM_UNIT
    )

    mock_system_rebuild_flow(mocker, unit_name)

    response = authorized_client.post(
        "/graphql",
        json={
            "query": query,
        },
    )
    data = get_data(response)["system"][f"runSystem{action.capitalize()}"]
    assert_ok(data)

    job_id = response.json()["data"]["system"][f"runSystem{action.capitalize()}"][
        "job"
    ]["uid"]
    assert Jobs.get_job(job_id).status == JobStatus.FINISHED
    assert Jobs.get_job(job_id).type_id == f"system.nixos.{action}"


@pytest.mark.parametrize("action", ["rebuild", "upgrade"])
def test_graphql_system_rebuild_failed(authorized_client, mocker, fp, action):
    """Test system rebuild"""
    query = (
        API_REBUILD_SYSTEM_MUTATION
        if action == "rebuild"
        else API_UPGRADE_SYSTEM_MUTATION
    )
    unit_name = (
        API_REBUILD_SYSTEM_UNIT if action == "rebuild" else API_UPGRADE_SYSTEM_UNIT
    )

    fp.register(
        ["journalctl", "-u", unit_name, "-n", "10", "-o", "cat"], stdout="Some error"
    )

    mock_system_rebuild_flow(mocker, unit_name, ServiceStatus.FAILED)

    response = authorized_client.post(
        "/graphql",
        json={
            "query": query,
        },
    )
    data = get_data(response)["system"][f"runSystem{action.capitalize()}"]
    assert_ok(data)

    job_id = response.json()["data"]["system"][f"runSystem{action.capitalize()}"][
        "job"
    ]["uid"]
    assert Jobs.get_job(job_id).status == JobStatus.ERROR
    assert Jobs.get_job(job_id).type_id == f"system.nixos.{action}"
    assert (
        Jobs.get_job(job_id).error
        == "System rebuild failed. Last log lines:\nSome error"
    )


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


def test_graphql_system_rollback_unauthorized(client, mocker):
    """Test system rollback without authorization"""

    def systemd_proxy():
        raise RuntimeError(
            "systemd_proxy shouldn't be used when calling rollback without authentication"
        )

    mocker.patch("selfprivacy_api.utils.systemd.systemd_proxy", systemd_proxy)

    response = client.post(
        "/graphql",
        json={
            "query": API_ROLLBACK_SYSTEM_MUTATION,
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_system_rollback(authorized_client, mocker):
    """Test system rollback"""

    rollback_unit_started = False

    class MockSystemdManager:
        async def start_unit(self, unit, method):
            nonlocal rollback_unit_started
            assert unit == "sp-nixos-rollback.service"
            assert method == "replace"

            rollback_unit_started = True

    mocker.patch(
        "selfprivacy_api.utils.systemd.systemd_proxy", lambda: MockSystemdManager()
    )

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
    assert rollback_unit_started


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


def test_graphql_reboot_system_unauthorized(client, mocker):
    reboot_started = False

    async def reboot():
        nonlocal reboot_started
        reboot_started = True

    mocker.patch("selfprivacy_api.actions.system.reboot_system", reboot)

    response = client.post(
        "/graphql",
        json={
            "query": API_REBOOT_SYSTEM_MUTATION,
        },
    )

    assert response.status_code == 200
    assert response.json().get("data") is None
    assert not reboot_started


def test_graphql_reboot_system(authorized_client, mocker):
    reboot_started = False

    async def reboot():
        nonlocal reboot_started
        reboot_started = True

    mocker.patch("selfprivacy_api.actions.system.reboot_system", reboot)

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REBOOT_SYSTEM_MUTATION,
        },
    )

    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["system"]["rebootSystem"]["success"] is True
    assert response.json()["data"]["system"]["rebootSystem"]["message"] is not None
    assert response.json()["data"]["system"]["rebootSystem"]["code"] == 200

    assert reboot_started
