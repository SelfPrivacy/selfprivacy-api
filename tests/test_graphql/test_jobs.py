from tests.common import generate_jobs_query
from tests.test_graphql.common import (
    assert_ok,
    assert_empty,
    assert_errorcode,
    get_data,
)

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


def test_all_jobs_unauthorized(client):
    response = graphql_send_query(client, generate_jobs_query([API_JOBS_QUERY]))
    assert_empty(response)


def test_all_jobs_when_none(authorized_client):
    output = api_jobs(authorized_client)
    assert output == []
