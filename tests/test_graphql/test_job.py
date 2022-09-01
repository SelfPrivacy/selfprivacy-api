import pytest


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():  # pylint: disable=no-method-argument
        return (b"NEW_HASHED", None)

    returncode = 0


class JobsMock:
    def remove_by_uuid(self, job_uuid: str):
        return True

class JobsMockReturnFalse:
    def remove_by_uuid(self, job_uuid: str):
        return False


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


@pytest.fixture
def mock_jobs(mocker):
    mock = mocker.patch("selfprivacy_api.jobs.__init__.Jobs", autospec=True, return_value=JobsMock)
    return mock

@pytest.fixture
def mock_jobs_return_false(mocker):
    mock = mocker.patch("selfprivacy_api.jobs.__init__.Jobs", autospec=True, return_value=JobsMock)
    return mock


API_REMOVE_JOB_MUTATION = """
mutation removeJob($sshInput: SshMutationInput!) {
    removeJob(sshInput: $sshInput) {
        success
        message
        code
    }
}
"""


def test_graphql_remove_job_unauthorized(client, mock_subprocess_popen, mock_jobs):
    response = client.post(
        "/graphql",
        json={
            "query": API_REMOVE_JOB_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "user1",
                    "sshKey": "ssh-rsa KEY test_key@pc",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_remove_job(authorized_client, mock_subprocess_popen, mock_jobs):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_JOB_MUTATION,
            "variables": {
                "job_id": "3301",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["removeJob"]["code"] == 200
    assert response.json()["data"]["removeJob"]["message"] is not None
    assert response.json()["data"]["removeJob"]["success"] is True

def test_graphql_remove_job_not_found(authorized_client, mock_subprocess_popen, mock_jobs_return_false):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_JOB_MUTATION,
            "variables": {
                "job_id": "3301",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["removeJob"]["code"] == 404
    assert response.json()["data"]["removeJob"]["message"] is not None
    assert response.json()["data"]["removeJob"]["success"] is False