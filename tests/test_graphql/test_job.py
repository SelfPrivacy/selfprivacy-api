import pytest
from selfprivacy_api.jobs.__init__ import Job


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():  # pylint: disable=no-method-argument
        return (b"NEW_HASHED", None)

    returncode = 0


class JobsMockReturnTrue:
    def __init__(self):
        pass

    def remove_by_uuid(self, job_uuid: str):
        return True


class JobsMockReturnFalse:
    def __init__(self):
        pass

    def remove_by_uuid(self, job_uuid: str):
        return False


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


@pytest.fixture
def mock_jobs_return_true(mocker):
    mock = mocker.patch(
        "selfprivacy_api.jobs.__init__.Jobs",
        autospec=True,
        return_value=JobsMockReturnTrue,
    )
    return mock


@pytest.fixture
def mock_jobs_return_false(mocker):
    mock = mocker.patch(
        "selfprivacy_api.jobs.__init__.Jobs",
        autospec=True,
        return_value=JobsMockReturnTrue,
    )
    return mock


API_REMOVE_JOB_MUTATION = """
mutation removeJob($job: Job!) {
    removeJob(job: $job) {
        success
        message
        code
    }
}
"""


def test_graphql_remove_job_unauthorized(
    client, mock_subprocess_popen, mock_jobs_return_true
):
    response = client.post(
        "/graphql",
        json={
            "query": API_REMOVE_JOB_MUTATION,
            "variables": {
                "Job": {
                    "uid": "12345",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_remove_job(
    authorized_client, mock_subprocess_popen, mock_jobs_return_true
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_JOB_MUTATION,
            "variables": {
                    "jobId": "12345",
                },
            },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None

    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["removeJob"]["code"] == 200
    assert response.json()["data"]["removeJob"]["message"] is not None
    assert response.json()["data"]["removeJob"]["success"] is True


def test_graphql_remove_job_not_found(
    authorized_client, mock_subprocess_popen, mock_jobs_return_false
):
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
