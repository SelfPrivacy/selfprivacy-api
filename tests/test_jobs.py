# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest
from time import sleep

from selfprivacy_api.jobs import Jobs, JobStatus
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job, translate_job
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


def test_not_zeroing_ttl(jobs_with_one_job):
    test_job = jobs_with_one_job.get_jobs()[0]
    jobs_with_one_job.set_expiration(test_job, 1)
    assert len(jobs_with_one_job.get_jobs()) == 1
    sleep(1.2)
    assert len(jobs_with_one_job.get_jobs()) == 0


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


def test_job_args_none_by_default(jobs_with_one_job):
    job = jobs_with_one_job.get_jobs()[0]
    assert job.name_args is None
    assert job.description_args is None


def test_job_args_survive_redis_roundtrip(jobs):
    job = jobs.add(
        name="Restore %(display_name)s",
        type_id="test.restore",
        description="Restoring %(display_name)s from %(snapshot_id)s",
        name_args={"display_name": "MyService"},
        description_args={"display_name": "MyService", "snapshot_id": "snap-123"},
    )
    retrieved = jobs.get_job(str(job.uid))
    assert retrieved is not None
    assert retrieved.name == "Restore %(display_name)s"
    assert retrieved.description == "Restoring %(display_name)s from %(snapshot_id)s"
    assert retrieved.name_args == {"display_name": "MyService"}
    assert retrieved.description_args == {
        "display_name": "MyService",
        "snapshot_id": "snap-123",
    }


def test_translate_job_interpolates_args(jobs):
    job = jobs.add(
        name="Backup %(display_name)s",
        type_id="test.backup",
        description="Backing up %(display_name)s",
        name_args={"display_name": "TestService"},
        description_args={"display_name": "TestService"},
    )
    translated = translate_job(job_to_api_job(job), locale="en")
    assert translated.name == "Backup TestService"
    assert translated.description == "Backing up TestService"


def test_translate_job_multi_key_description_args(jobs):
    job = jobs.add(
        name="Restore %(display_name)s",
        type_id="test.restore",
        description="Restoring %(display_name)s from %(snapshot_id)s",
        name_args={"display_name": "Nextcloud"},
        description_args={"display_name": "Nextcloud", "snapshot_id": "abc-123"},
    )
    translated = translate_job(job_to_api_job(job), locale="en")
    assert translated.name == "Restore Nextcloud"
    assert translated.description == "Restoring Nextcloud from abc-123"


def test_translate_job_without_args_unchanged(jobs):
    job = jobs.add(
        name="Total backup",
        type_id="test.total",
        description="Backing up all enabled services",
    )
    translated = translate_job(job_to_api_job(job), locale="en")
    assert translated.name == "Total backup"
    assert translated.description == "Backing up all enabled services"


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
