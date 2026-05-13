from selfprivacy_api.jobs import Jobs, JobStatus

from tests.common import generate_jobs_query
from tests.test_graphql.common import (
    assert_empty,
    get_data,
)
from tests.test_jobs import jobs


API_JOBS_QUERY = """
getJobs {
    uid
    typeId
    name
    description
    status
    statusText
    progress
    createdAt
    updatedAt
    finishedAt
    error
    result
}
"""


def graphql_send_query(client, query: str, variables: dict = {}):
    return client.post("/graphql", json={"query": query, "variables": variables})


def api_jobs(authorized_client):
    response = graphql_send_query(
        authorized_client, generate_jobs_query([API_JOBS_QUERY])
    )
    data = get_data(response)
    result = data["jobs"]["getJobs"]
    assert result is not None
    return result


def test_all_jobs_unauthorized(client, jobs):
    response = graphql_send_query(client, generate_jobs_query([API_JOBS_QUERY]))
    assert_empty(response)


def test_all_jobs_when_none(authorized_client, jobs):
    output = api_jobs(authorized_client)
    assert output == []


def test_all_jobs_when_some(authorized_client, jobs):
    # We cannot make new jobs via API, at least directly
    job = Jobs.add("bogus", "bogus.bogus", "fungus")
    output = api_jobs(authorized_client)

    assert len(output) == 1
    api_job = output[0]

    assert api_job["uid"] == str(job.uid)
    assert api_job["typeId"] == job.type_id
    assert api_job["name"] == job.name
    assert api_job["description"] == job.description
    assert api_job["status"] == job.status
    assert api_job["statusText"] == job.status_text
    assert api_job["progress"] == job.progress
    assert api_job["createdAt"] == job.created_at.isoformat()
    assert api_job["updatedAt"] == job.updated_at.isoformat()
    assert api_job["finishedAt"] == None
    assert api_job["error"] == None
    assert api_job["result"] == None


def test_job_args_interpolated_in_graphql_response(authorized_client, jobs):
    job = Jobs.add(
        name="Backup %(display_name)s",
        type_id="test.backup",
        description="Backing up %(display_name)s",
        name_args={"display_name": "Nextcloud"},
        description_args={"display_name": "Nextcloud"},
    )
    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Found %(dead_packages)s packages to remove!",
        status_text_args={"dead_packages": 7},
    )
    Jobs.update(
        job=job,
        status=JobStatus.ERROR,
        error="Block device %(block_device_name)s not found.",
        error_args={"block_device_name": "sdb"},
        result="%(size_in_megabytes)s have been cleared",
        result_args={"size_in_megabytes": "339.84 MiB"},
    )
    output = api_jobs(authorized_client)
    assert len(output) == 1
    assert output[0]["name"] == "Backup Nextcloud"
    assert output[0]["description"] == "Backing up Nextcloud"
    assert output[0]["statusText"] == "Found 7 packages to remove!"
    assert output[0]["error"] == "Block device sdb not found."
    assert output[0]["result"] == "339.84 MiB have been cleared"


def test_job_without_args_unaffected_in_graphql_response(authorized_client, jobs):
    Jobs.add("Total backup", "test.total", "Backing up all enabled services")
    output = api_jobs(authorized_client)
    assert len(output) == 1
    assert output[0]["name"] == "Total backup"
    assert output[0]["description"] == "Backing up all enabled services"
