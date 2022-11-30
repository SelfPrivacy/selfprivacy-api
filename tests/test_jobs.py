# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest

from selfprivacy_api.jobs import Jobs, JobStatus
import selfprivacy_api.jobs as jobsmodule


def test_add_reset(jobs_with_one_job):
    jobs_with_one_job.reset()
    assert jobs_with_one_job.get_jobs() == []


def test_minimal_update(jobs_with_one_job):
    jobs = jobs_with_one_job
    test_job = jobs_with_one_job.get_jobs()[0]

    jobs.update(job=test_job, status=JobStatus.ERROR)

    assert jobs.get_jobs() == [test_job]


def test_jobs(jobs_with_one_job):
    jobs = jobs_with_one_job
    test_job = jobs_with_one_job.get_jobs()[0]

    jobs.update(
        job=test_job,
        name="Write Tests",
        description="An oddly satisfying experience",
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
def jobs():
    j = Jobs()
    j.reset()
    assert j.get_jobs() == []
    yield j
    j.reset()


@pytest.fixture
def jobs_with_one_job(jobs):
    test_job = jobs.add(
        type_id="test",
        name="Test job",
        description="This is a test job.",
        status=JobStatus.CREATED,
        status_text="Status text",
        progress=0,
    )
    assert jobs.get_jobs() == [test_job]
    return jobs
