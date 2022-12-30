"""Jobs status"""
# pylint: disable=too-few-public-methods
import datetime
import typing
import strawberry

from selfprivacy_api.jobs import Job, Jobs


@strawberry.type
class ApiJob:
    """Job type for GraphQL."""

    uid: str
    name: str
    description: str
    status: str
    status_text: typing.Optional[str]
    progress: typing.Optional[int]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    finished_at: typing.Optional[datetime.datetime]
    error: typing.Optional[str]
    result: typing.Optional[str]


def job_to_api_job(job: Job) -> ApiJob:
    """Convert a Job from jobs controller to a GraphQL ApiJob."""
    return ApiJob(
        uid=str(job.uid),
        name=job.name,
        description=job.description,
        status=job.status.name,
        status_text=job.status_text,
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        finished_at=job.finished_at,
        error=job.error,
        result=job.result,
    )


def get_api_job_by_id(job_id: str) -> typing.Optional[ApiJob]:
    """Get a job for GraphQL by its ID."""
    job = Jobs.get_job(job_id)
    if job is None:
        return None
    return job_to_api_job(job)
