"""Jobs status"""

# pylint: disable=too-few-public-methods
import datetime
from opentelemetry import trace
from typing import Optional
import strawberry

from selfprivacy_api.jobs import Job, Jobs

tracer = trace.get_tracer(__name__)


@strawberry.type
class ApiJob:
    """Job type for GraphQL."""

    uid: str
    type_id: str
    name: str
    description: str
    status: str
    status_text: Optional[str]
    progress: Optional[int]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    finished_at: Optional[datetime.datetime]
    error: Optional[str]
    result: Optional[str]


def job_to_api_job(job: Job) -> ApiJob:
    """Convert a Job from jobs controller to a GraphQL ApiJob."""
    return ApiJob(
        uid=str(job.uid),
        type_id=job.type_id,
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


async def get_api_job_by_id(job_id: str) -> Optional[ApiJob]:
    """Get a job for GraphQL by its ID."""
    with tracer.start_as_current_span(
        "get_api_job_by_id", attributes={"job_id": job_id}
    ):
        job = Jobs.get_job(job_id)
        if job is None:
            return None
        return job_to_api_job(job)
