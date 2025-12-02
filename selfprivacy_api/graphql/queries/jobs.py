"""Jobs status"""

# pylint: disable=too-few-public-methods
import strawberry
from typing import List, Optional
from opentelemetry import trace

from selfprivacy_api.jobs import Jobs
from selfprivacy_api.graphql.common_types.jobs import (
    ApiJob,
    get_api_job_by_id,
    job_to_api_job,
)

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("resolve_get_all_jobs")
async def get_all_jobs() -> List[ApiJob]:
    jobs = Jobs.get_jobs()
    api_jobs = [job_to_api_job(job) for job in jobs]
    assert api_jobs is not None
    return api_jobs


@strawberry.type
class Job:
    @strawberry.field
    async def get_jobs(self) -> List[ApiJob]:
        return await get_all_jobs()

    @strawberry.field
    async def get_job(self, job_id: str) -> Optional[ApiJob]:
        return await get_api_job_by_id(job_id)
