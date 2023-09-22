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


def test_remove_by_uid(jobs_with_one_job):
    test_job = jobs_with_one_job.get_jobs()[0]
    uid_str = str(test_job.uid)

    assert jobs_with_one_job.remove_by_uid(uid_str)
    assert jobs_with_one_job.get_jobs() == []
    assert not jobs_with_one_job.remove_by_uid(uid_str)


def test_remove_update_nonexistent(jobs_with_one_job):
    test_job = jobs_with_one_job.get_jobs()[0]

    jobs_with_one_job.remove(test_job)
    assert jobs_with_one_job.get_jobs() == []

    result = jobs_with_one_job.update(job=test_job, status=JobStatus.ERROR)
    assert result == test_job  # even though we might consider changing this behavior


def test_remove_get_nonexistent(jobs_with_one_job):
    test_job = jobs_with_one_job.get_jobs()[0]
    uid_str = str(test_job.uid)
    assert jobs_with_one_job.get_job(uid_str) == test_job

    jobs_with_one_job.remove(test_job)

    assert jobs_with_one_job.get_job(uid_str) is None


def test_set_zeroing_ttl(jobs_with_one_job):
    test_job = jobs_with_one_job.get_jobs()[0]
    jobs_with_one_job.set_expiration(test_job, 0)
    assert jobs_with_one_job.get_jobs() == []


def test_jobs(jobs_with_one_job):
    jobs = jobs_with_one_job
    test_job = jobs_with_one_job.get_jobs()[0]
    assert not jobs.is_busy()

    jobs.update(
        job=test_job,
        name="Write Tests",
        description="An oddly satisfying experience",
        status=JobStatus.RUNNING,
        status_text="Status text",
        progress=50,
    )

    assert jobs.get_jobs() == [test_job]
    assert jobs.is_busy()

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


def test_finishing_equals_100(jobs_with_one_job):
    jobs = jobs_with_one_job
    test_job = jobs.get_jobs()[0]
    assert not jobs.is_busy()
    assert test_job.progress != 100

    jobs.update(job=test_job, status=JobStatus.FINISHED)

    assert test_job.progress == 100


def test_finishing_equals_100_unless_stated_otherwise(jobs_with_one_job):
    jobs = jobs_with_one_job
    test_job = jobs.get_jobs()[0]
    assert not jobs.is_busy()
    assert test_job.progress != 100
    assert test_job.progress != 23

    jobs.update(job=test_job, status=JobStatus.FINISHED, progress=23)

    assert test_job.progress == 23


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
