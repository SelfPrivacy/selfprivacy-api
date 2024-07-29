from os import path
from tests.test_backup import backups
from tests.common import generate_backup_query


import selfprivacy_api.services as all_services
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.graphql.common_types.service import service_to_graphql_service
from selfprivacy_api.graphql.common_types.backup import (
    _AutobackupQuotas,
    AutobackupQuotas,
)
from selfprivacy_api.jobs import Jobs, JobStatus
from selfprivacy_api.backup.storage import Storage
from selfprivacy_api.backup.local_secret import LocalBackupSecret

from tests.test_graphql.test_services import (
    only_dummy_service_and_api,
    only_dummy_service,
    dkim_file,
)


API_RELOAD_SNAPSHOTS = """
mutation TestSnapshotsReload {
    backup {
        forceSnapshotsReload {
            success
            message
            code
        }
    }
}
"""

API_MANUAL_AUTOBACKUP = """
mutation TestForcedAutobackup {
    backup {
         manualAutobackup{
            success
            message
            code
        }
    }
}
"""

API_SET_AUTOBACKUP_PERIOD_MUTATION = """
mutation TestAutobackupPeriod($period: Int) {
    backup {
        setAutobackupPeriod(period: $period) {
            success
            message
            code
            configuration {
                provider
                encryptionKey
                isInitialized
                autobackupPeriod
                locationName
                locationId
            }
        }
    }
}
"""


API_SET_AUTOBACKUP_QUOTAS_MUTATION = """
mutation TestAutobackupQuotas($input: AutobackupQuotasInput!) {
    backup {
        setAutobackupQuotas(quotas: $input) {
            success
            message
            code
            configuration {
                provider
                encryptionKey
                isInitialized
                autobackupPeriod
                locationName
                locationId
                autobackupQuotas {
                    last
                    daily
                    weekly
                    monthly
                    yearly
                }
            }
        }
    }
}
"""

API_REMOVE_REPOSITORY_MUTATION = """
mutation TestRemoveRepo {
    backup {
        removeRepository {
            success
            message
            code
            configuration {
                provider
                encryptionKey
                isInitialized
                autobackupPeriod
                locationName
                locationId
            }
        }
    }
}
"""

API_INIT_MUTATION = """
mutation TestInitRepo($input: InitializeRepositoryInput!) {
    backup {
        initializeRepository(repository: $input) {
            success
            message
            code
            configuration {
                provider
                encryptionKey
                isInitialized
                autobackupPeriod
                locationName
                locationId
            }
        }
    }
}
"""

API_RESTORE_MUTATION = """
mutation TestRestoreService($snapshot_id: String!) {
    backup {
        restoreBackup(snapshotId: $snapshot_id) {
            success
            message
            code
            job {
                uid
                status
            }
        }
    }
}
"""

API_FORGET_MUTATION = """
mutation TestForgetSnapshot($snapshot_id: String!) {
    backup {
        forgetSnapshot(snapshotId: $snapshot_id) {
            success
            message
            code
        }
    }
}
"""

API_SNAPSHOTS_QUERY = """
allSnapshots {
    id
    service {
        id
        displayName
    }
    createdAt
    reason
}
"""

API_BACKUP_SETTINGS_QUERY = """
configuration {
        provider
        encryptionKey
        isInitialized
        autobackupPeriod
        locationName
        locationId
    }
"""

API_BACK_UP_MUTATION = """
mutation TestBackupService($service_id: String!) {
    backup {
        startBackup(serviceId: $service_id) {
            success
            message
            code
            job {
                uid
                status
            }
        }
    }
}
"""


def api_restore(authorized_client, snapshot_id):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESTORE_MUTATION,
            "variables": {"snapshot_id": snapshot_id},
        },
    )
    return response


def api_backup(authorized_client, service):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_BACK_UP_MUTATION,
            "variables": {"service_id": service.get_id()},
        },
    )
    return response


def api_forget(authorized_client, snapshot_id):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_FORGET_MUTATION,
            "variables": {"snapshot_id": snapshot_id},
        },
    )
    return response


def api_set_period(authorized_client, period):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_SET_AUTOBACKUP_PERIOD_MUTATION,
            "variables": {"period": period},
        },
    )
    return response


def api_set_quotas(authorized_client, quotas: _AutobackupQuotas):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_SET_AUTOBACKUP_QUOTAS_MUTATION,
            "variables": {"input": quotas.model_dump()},
        },
    )
    return response


def api_remove(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_REPOSITORY_MUTATION,
            "variables": {},
        },
    )
    return response


def api_reload_snapshots(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RELOAD_SNAPSHOTS,
            "variables": {},
        },
    )
    return response


def api_manual_autobackup(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MANUAL_AUTOBACKUP,
            "variables": {},
        },
    )
    return response


def api_init(
    authorized_client,
    kind,
    login,
    password,
    location_name,
    location_id,
    local_secret=None,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_INIT_MUTATION,
            "variables": {
                "input": {
                    "provider": kind,
                    "locationId": location_id,
                    "locationName": location_name,
                    "login": login,
                    "password": password,
                    "localSecret": local_secret,
                }
            },
        },
    )
    return response


def assert_ok(data):
    if data["success"] is False:
        # convenience for debugging, this should display error
        # if empty, consider adding helpful messages
        raise ValueError(data["code"], data["message"])
    assert data["code"] == 200
    assert data["success"] is True


def get_data(response):
    assert response.status_code == 200
    response = response.json()
    if (
        "errors" in response.keys()
    ):  # convenience for debugging, this will display error
        raise ValueError(response["errors"])
    assert response["data"] is not None
    data = response["data"]
    return data


def api_snapshots(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_backup_query([API_SNAPSHOTS_QUERY])},
    )
    data = get_data(response)
    result = data["backup"]["allSnapshots"]
    assert result is not None
    return result


def api_settings(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_backup_query([API_BACKUP_SETTINGS_QUERY])},
    )
    data = get_data(response)
    result = data["backup"]["configuration"]
    assert result is not None
    return result


def test_dummy_service_convertible_to_gql(dummy_service):
    gql_service = service_to_graphql_service(dummy_service)
    assert gql_service is not None


def test_snapshots_empty(authorized_client, dummy_service, backups):
    snaps = api_snapshots(authorized_client)
    assert snaps == []


def test_snapshots_orphaned_service(authorized_client, dummy_service, backups):
    api_backup(authorized_client, dummy_service)
    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 1

    all_services.services.remove(dummy_service)
    assert ServiceManager.get_service_by_id(dummy_service.get_id()) is None

    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 1
    assert "Orphaned" in snaps[0]["service"]["displayName"]
    assert dummy_service.get_id() in snaps[0]["service"]["displayName"]


def test_start_backup(authorized_client, dummy_service, backups):
    response = api_backup(authorized_client, dummy_service)
    data = get_data(response)["backup"]["startBackup"]
    assert data["success"] is True
    job = data["job"]

    assert Jobs.get_job(job["uid"]).status == JobStatus.FINISHED
    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 1
    snap = snaps[0]

    assert snap["id"] is not None
    assert snap["id"] != ""
    assert snap["service"]["id"] == "testservice"


def test_restore(authorized_client, dummy_service, backups):
    api_backup(authorized_client, dummy_service)
    snap = api_snapshots(authorized_client)[0]
    assert snap["id"] is not None

    response = api_restore(authorized_client, snap["id"])
    data = get_data(response)["backup"]["restoreBackup"]
    assert data["success"] is True
    job = data["job"]

    assert Jobs.get_job(job["uid"]).status == JobStatus.FINISHED


def test_reinit(authorized_client, dummy_service, tmpdir, backups):
    test_repo_path = path.join(tmpdir, "not_at_all_sus")
    response = api_init(authorized_client, "FILE", "", "", test_repo_path, "")
    data = get_data(response)["backup"]["initializeRepository"]
    assert_ok(data)
    configuration = data["configuration"]
    assert configuration["provider"] == "FILE"
    assert configuration["locationId"] == ""
    assert configuration["locationName"] == test_repo_path
    assert len(configuration["encryptionKey"]) > 1
    assert configuration["isInitialized"] is True

    response = api_backup(authorized_client, dummy_service)
    data = get_data(response)["backup"]["startBackup"]
    assert data["success"] is True
    job = data["job"]

    assert Jobs.get_job(job["uid"]).status == JobStatus.FINISHED


def test_migrate_backup_repo(authorized_client, dummy_service, tmpdir, backups):
    """
    Simulate the workflow of migrating to a new server
    """
    # Using an alternative path to be sure that we do not
    # match only by incident
    test_repo_path = path.join(tmpdir, "not_at_all_sus")
    response = api_init(authorized_client, "FILE", "", "", test_repo_path, "")
    data = get_data(response)["backup"]["initializeRepository"]
    assert_ok(data)
    snaps = api_snapshots(authorized_client)
    assert snaps == []

    # Now, forget what we just did
    del test_repo_path
    del response
    del data
    del snaps

    # I am a user at my old machine, I make a backup
    response = api_backup(authorized_client, dummy_service)
    data = get_data(response)["backup"]["startBackup"]
    assert_ok(data)

    # Then oh no, we need to migrate, we get our settings.
    # Because we have forgot everything 2000 times already
    # Was years, was years.
    # I still remember login though
    configuration = api_settings(authorized_client)

    # Ok. Let's now go to another machine
    # Another machine will not have any settings at all

    Storage.reset()
    LocalBackupSecret._full_reset()

    # That's it, nothing left
    new_configuration = api_settings(authorized_client)
    assert new_configuration["isInitialized"] is False

    # Reinit
    response = api_init(
        authorized_client,
        kind=configuration["provider"],
        login="",  # user provides login and password, configuration endpoint does not
        password="",  # empty for file based repository
        location_name=configuration["locationName"],
        location_id=configuration["locationId"],
        local_secret=configuration["encryptionKey"],
    )
    data = get_data(response)["backup"]["initializeRepository"]
    assert_ok(data)
    assert data["configuration"] == configuration

    new_configuration = api_settings(authorized_client)
    assert new_configuration == configuration

    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 1


def test_remove(authorized_client, generic_userdata, backups):
    response = api_remove(authorized_client)
    data = get_data(response)["backup"]["removeRepository"]
    assert_ok(data)

    configuration = data["configuration"]
    assert configuration["provider"] == "NONE"
    assert configuration["locationId"] == ""
    assert configuration["locationName"] == ""
    # still generated every time it is missing
    assert len(configuration["encryptionKey"]) > 1
    assert configuration["isInitialized"] is False


def test_autobackup_quotas_nonzero(authorized_client, backups):
    quotas = _AutobackupQuotas(
        last=3,
        daily=2,
        weekly=4,
        monthly=13,
        yearly=14,
    )
    response = api_set_quotas(authorized_client, quotas)
    data = get_data(response)["backup"]["setAutobackupQuotas"]
    assert_ok(data)

    configuration = data["configuration"]
    assert configuration["autobackupQuotas"] == quotas.model_dump()


def test_autobackup_period_nonzero(authorized_client, backups):
    new_period = 11
    response = api_set_period(authorized_client, new_period)
    data = get_data(response)["backup"]["setAutobackupPeriod"]
    assert_ok(data)

    configuration = data["configuration"]
    assert configuration["autobackupPeriod"] == new_period


def test_autobackup_period_zero(authorized_client, backups):
    new_period = 0
    # since it is none by default, we better first set it to something non-negative
    response = api_set_period(authorized_client, 11)
    # and now we nullify it
    response = api_set_period(authorized_client, new_period)
    data = get_data(response)["backup"]["setAutobackupPeriod"]
    assert_ok(data)

    configuration = data["configuration"]
    assert configuration["autobackupPeriod"] == None


def test_autobackup_period_none(authorized_client, backups):
    # since it is none by default, we better first set it to something non-negative
    response = api_set_period(authorized_client, 11)
    # and now we nullify it
    response = api_set_period(authorized_client, None)
    data = get_data(response)["backup"]["setAutobackupPeriod"]
    assert_ok(data)

    configuration = data["configuration"]
    assert configuration["autobackupPeriod"] == None


def test_autobackup_period_negative(authorized_client, backups):
    # since it is none by default, we better first set it to something non-negative
    response = api_set_period(authorized_client, 11)
    # and now we nullify it
    response = api_set_period(authorized_client, -12)
    data = get_data(response)["backup"]["setAutobackupPeriod"]
    assert_ok(data)

    configuration = data["configuration"]
    assert configuration["autobackupPeriod"] == None


# We cannot really check the effect at this level, we leave it to backend tests
# But we still make it run in both empty and full scenarios and ask for snaps afterwards
def test_reload_snapshots_bare_bare_bare(authorized_client, dummy_service, backups):
    api_remove(authorized_client)

    response = api_reload_snapshots(authorized_client)
    data = get_data(response)["backup"]["forceSnapshotsReload"]
    assert_ok(data)

    snaps = api_snapshots(authorized_client)
    assert snaps == []


def test_induce_autobackup(authorized_client, only_dummy_service_and_api, backups):
    dummy_service = only_dummy_service_and_api

    response = api_manual_autobackup(authorized_client)
    # raise ValueError(get_data(response))
    data = get_data(response)["backup"]["manualAutobackup"]
    assert_ok(data)

    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 2


def test_reload_snapshots(authorized_client, dummy_service, backups):
    response = api_backup(authorized_client, dummy_service)
    data = get_data(response)["backup"]["startBackup"]

    response = api_reload_snapshots(authorized_client)
    data = get_data(response)["backup"]["forceSnapshotsReload"]
    assert_ok(data)

    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 1


def test_forget_snapshot(authorized_client, dummy_service, backups):
    response = api_backup(authorized_client, dummy_service)
    data = get_data(response)["backup"]["startBackup"]

    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 1

    response = api_forget(authorized_client, snaps[0]["id"])
    data = get_data(response)["backup"]["forgetSnapshot"]
    assert_ok(data)

    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 0


def test_forget_nonexistent_snapshot(authorized_client, dummy_service, backups):
    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 0
    response = api_forget(authorized_client, "898798uekiodpjoiweoiwuoeirueor")
    data = get_data(response)["backup"]["forgetSnapshot"]
    assert data["code"] == 404
    assert data["success"] is False

    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 0
