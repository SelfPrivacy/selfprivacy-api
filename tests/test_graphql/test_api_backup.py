from os import path
from tests.test_graphql.test_backup import dummy_service, backups, raw_dummy_service
from tests.common import generate_backup_query


from selfprivacy_api.graphql.common_types.service import service_to_graphql_service
from selfprivacy_api.jobs import Jobs, JobStatus

API_REMOVE_REPOSITORY_MUTATION = """
mutation TestRemoveRepo {
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
"""

API_INIT_MUTATION = """
mutation TestInitRepo($input: InitializeRepositoryInput!) {
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
"""

API_RESTORE_MUTATION = """
mutation TestRestoreService($snapshot_id: String!) {
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
"""

API_SNAPSHOTS_QUERY = """
allSnapshots {
    id
    service {
        id
    }
    createdAt
}
"""

API_BACK_UP_MUTATION = """
mutation TestBackupService($service_id: String!) {
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


def api_remove(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_REPOSITORY_MUTATION,
            "variables": {},
        },
    )
    return response


def api_init_without_key(
    authorized_client, kind, login, password, location_name, location_id
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
                }
            },
        },
    )
    return response


def assert_ok(data):
    assert data["code"] == 200
    assert data["success"] is True


def get_data(response):
    assert response.status_code == 200
    response = response.json()
    if (
        "errors" in response.keys()
    ):  # convenience for debugging, this will display error
        assert response["errors"] == []
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


def test_dummy_service_convertible_to_gql(dummy_service):
    gql_service = service_to_graphql_service(dummy_service)
    assert gql_service is not None


def test_snapshots_empty(authorized_client, dummy_service):
    snaps = api_snapshots(authorized_client)
    assert snaps == []


def test_start_backup(authorized_client, dummy_service):
    response = api_backup(authorized_client, dummy_service)
    data = get_data(response)["startBackup"]
    assert data["success"] is True
    job = data["job"]

    assert Jobs.get_job(job["uid"]).status == JobStatus.FINISHED
    snaps = api_snapshots(authorized_client)
    assert len(snaps) == 1
    snap = snaps[0]

    assert snap["id"] is not None
    assert snap["id"] != ""
    assert snap["service"]["id"] == "testservice"


def test_restore(authorized_client, dummy_service):
    api_backup(authorized_client, dummy_service)
    snap = api_snapshots(authorized_client)[0]
    assert snap["id"] is not None

    response = api_restore(authorized_client, snap["id"])
    data = get_data(response)["restoreBackup"]
    assert data["success"] is True
    job = data["job"]

    assert Jobs.get_job(job["uid"]).status == JobStatus.FINISHED


def test_reinit(authorized_client, dummy_service, tmpdir):
    test_repo_path = path.join(tmpdir, "not_at_all_sus")
    response = api_init_without_key(
        authorized_client, "FILE", "", "", test_repo_path, ""
    )
    data = get_data(response)["initializeRepository"]
    assert_ok(data)
    configuration = data["configuration"]
    assert configuration["provider"] == "FILE"
    assert configuration["locationId"] == ""
    assert configuration["locationName"] == test_repo_path
    assert len(configuration["encryptionKey"]) > 1
    assert configuration["isInitialized"] is True

    response = api_backup(authorized_client, dummy_service)
    data = get_data(response)["startBackup"]
    assert data["success"] is True
    job = data["job"]

    assert Jobs.get_job(job["uid"]).status == JobStatus.FINISHED


def test_remove(authorized_client, generic_userdata):
    response = api_remove(authorized_client)
    data = get_data(response)["removeRepository"]
    assert_ok(data)

    configuration = data["configuration"]
    assert configuration["provider"] == "BACKBLAZE"
    assert configuration["locationId"] == ""
    assert configuration["locationName"] == "selfprivacy"
    # still generated every time it is missing
    assert len(configuration["encryptionKey"]) > 1
    assert configuration["isInitialized"] is False
