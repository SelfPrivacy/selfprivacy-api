from tests.test_graphql.test_backup import dummy_service, backups, raw_dummy_service
from tests.common import generate_backup_query


from selfprivacy_api.graphql.common_types.service import service_to_graphql_service
from selfprivacy_api.jobs import Jobs, JobStatus

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
mutation TestBackupService($service_id: String) {
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


def api_backup(authorized_client, service):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_BACK_UP_MUTATION,
            "variables": {"service_id": service.get_id()},
        },
    )
    return response


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
    assert snap["service"]["id"] == "testservice"
