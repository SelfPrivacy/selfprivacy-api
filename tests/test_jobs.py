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


def test_update_name_and_description_args(jobs):
    job = jobs.add(
        name="Backup %(display_name)s",
        type_id="test.backup",
        description="Backing up %(display_name)s",
        name_args={"display_name": "Nextcloud"},
        description_args={"display_name": "Nextcloud"},
    )
    jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        name="Move %(service)s",
        name_args={"service": "Bitwarden"},
        description="Moving %(service)s data to %(volume)s",
        description_args={"service": "Bitwarden", "volume": "sdb"},
    )
    retrieved = jobs.get_job(str(job.uid))
    assert retrieved is not None
    assert retrieved.name == "Move %(service)s"
    assert retrieved.name_args == {"service": "Bitwarden"}
    assert retrieved.description == "Moving %(service)s data to %(volume)s"
    assert retrieved.description_args == {"service": "Bitwarden", "volume": "sdb"}
    translated = translate_job(job_to_api_job(retrieved), locale="en")
    assert translated.name == "Move Bitwarden"
    assert translated.description == "Moving Bitwarden data to sdb"


def test_job_args_none_by_default(jobs_with_one_job):
    job = jobs_with_one_job.get_jobs()[0]
    assert job.name_args is None
    assert job.description_args is None
    assert job.status_text_args is None
    assert job.error_args is None
    assert job.result_args is None


def test_job_args_survive_redis_roundtrip(jobs):
    job = jobs.add(
        name="Restore %(display_name)s",
        type_id="test.restore",
        description="Restoring %(display_name)s from %(snapshot_id)s",
        name_args={"display_name": "MyService"},
        description_args={"display_name": "MyService", "snapshot_id": "snap-123"},
    )
    jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Found %(dead_packages)s packages to remove!",
        status_text_args={"dead_packages": 42},
    )
    jobs.update(
        job=job,
        status=JobStatus.ERROR,
        error="Block device %(block_device_name)s not found.",
        error_args={"block_device_name": "sdb"},
        result="%(size_in_megabytes)s have been cleared",
        result_args={"size_in_megabytes": "1.2 GB"},
    )
    retrieved = jobs.get_job(str(job.uid))
    assert retrieved is not None
    assert retrieved.name == "Restore %(display_name)s"
    assert retrieved.name_args == {"display_name": "MyService"}
    assert retrieved.description == "Restoring %(display_name)s from %(snapshot_id)s"
    assert retrieved.description_args == {
        "display_name": "MyService",
        "snapshot_id": "snap-123",
    }
    assert retrieved.status_text == "Found %(dead_packages)s packages to remove!"
    assert retrieved.status_text_args == {"dead_packages": 42}
    assert retrieved.error == "Block device %(block_device_name)s not found."
    assert retrieved.error_args == {"block_device_name": "sdb"}
    assert retrieved.result == "%(size_in_megabytes)s have been cleared"
    assert retrieved.result_args == {"size_in_megabytes": "1.2 GB"}


def test_translate_job_interpolates_args(jobs):
    job = jobs.add(
        name="Backup %(display_name)s",
        type_id="test.backup",
        description="Backing up %(display_name)s from %(snapshot_id)s",
        name_args={"display_name": "Nextcloud"},
        description_args={"display_name": "Nextcloud", "snapshot_id": "abc-123"},
    )
    jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Found %(dead_packages)s packages to remove!",
        status_text_args={"dead_packages": 15},
    )
    jobs.update(
        job=job,
        status=JobStatus.ERROR,
        error="Block device %(block_device_name)s not found.",
        error_args={"block_device_name": "sdb"},
        result="%(size_in_megabytes)s have been cleared",
        result_args={"size_in_megabytes": "339.84 MiB"},
    )
    translated = translate_job(job_to_api_job(job), locale="en")
    assert translated.name == "Backup Nextcloud"
    assert translated.description == "Backing up Nextcloud from abc-123"
    assert translated.status_text == "Found 15 packages to remove!"
    assert translated.error == "Block device sdb not found."
    assert translated.result == "339.84 MiB have been cleared"


def test_translate_job_without_args_unchanged(jobs):
    job = jobs.add(
        name="Total backup",
        type_id="test.total",
        description="Backing up all enabled services",
    )
    jobs.update(
        job=job,
        status=JobStatus.FINISHED,
        status_text="Done",
        result="System is clear",
        error=None,
    )
    translated = translate_job(job_to_api_job(job), locale="en")
    assert translated.name == "Total backup"
    assert translated.description == "Backing up all enabled services"
    assert translated.status_text == "Done"
    assert translated.result == "System is clear"
    assert translated.error is None


def test_translate_job_status_text_args_cleared_on_update(jobs):
    job = jobs.add(name="Some job", type_id="test.job", description="Doing things")
    jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Found %(dead_packages)s packages to remove!",
        status_text_args={"dead_packages": 15},
    )
    jobs.update(job=job, status=JobStatus.RUNNING, status_text="Cleaning...")
    translated = translate_job(job_to_api_job(job), locale="en")
    assert translated.status_text == "Cleaning..."


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
