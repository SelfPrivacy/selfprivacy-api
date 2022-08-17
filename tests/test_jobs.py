# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import json
import pytest

from selfprivacy_api.utils import WriteUserData, ReadUserData
from selfprivacy_api.jobs import Jobs, JobStatus


def test_jobs(authorized_client, jobs_file, shared_datadir):
    jobs = Jobs()
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
