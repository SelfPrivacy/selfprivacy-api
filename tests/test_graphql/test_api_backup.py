from tests.test_graphql.test_backup import dummy_service, backups, raw_dummy_service

# from tests.common import generate_api_query

# from selfprivacy_api.graphql.mutations.backup_mutations import BackupMutations
from selfprivacy_api.jobs import Jobs, JobStatus

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
    ).json()
    return response


def test_start_backup(authorized_client, dummy_service):
    response = api_backup(authorized_client, dummy_service)
    assert response["data"]["startBackup"]["success"] is True
    job = response["data"]["startBackup"]["job"]
    assert Jobs.get_job(job["uid"]).status == JobStatus.FINISHED
