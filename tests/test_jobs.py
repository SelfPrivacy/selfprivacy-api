# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest

from selfprivacy_api.jobs import Jobs, JobStatus
import selfprivacy_api.jobs as jobsmodule


def test_jobs(authorized_client, jobs_file, shared_datadir):
    jobs = Jobs()
    jobs.reset()
    assert jobs.get_jobs() == []

    test_job = jobs.add(
        type_id="test",
        name="Test job",
        description="This is a test job.",
        status=JobStatus.CREATED,
        status_text="Status text",
        progress=0,
    )

    assert jobs.get_jobs() == [test_job]

    jobs.update(
        job=test_job,
        status=JobStatus.RUNNING,
        status_text="Status text",
        progress=50,
    )

    assert jobs.get_jobs() == [test_job]

    backup = jobsmodule.JOB_EXPIRATION_SECONDS
    jobsmodule.JOB_EXPIRATION_SECONDS = 0

    jobs.update(
        job=test_job,
        status=JobStatus.FINISHED,
        status_text="Yaaay!",
        progress=100,
    )

    assert jobs.get_jobs() == []
    jobsmodule.JOB_EXPIRATION_SECONDS = backup


@pytest.fixture
def mock_subprocess_run(mocker):
    mock = mocker.patch("subprocess.run", autospec=True)
    return mock


@pytest.fixture
def mock_shutil_move(mocker):
    mock = mocker.patch("shutil.move", autospec=True)
    return mock


@pytest.fixture
def mock_shutil_chown(mocker):
    mock = mocker.patch("shutil.chown", autospec=True)
    return mock
