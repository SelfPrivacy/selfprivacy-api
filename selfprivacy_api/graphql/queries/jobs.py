"""Jobs status"""
# pylint: disable=too-few-public-methods
import strawberry
from typing import List, Optional

from selfprivacy_api.jobs import Jobs
from selfprivacy_api.graphql.common_types.jobs import (
    ApiJob,
    get_api_job_by_id,
    job_to_api_job,
)


def get_all_jobs() -> List[ApiJob]:
    jobs = Jobs.get_jobs()
    api_jobs = [job_to_api_job(job) for job in jobs]
    assert api_jobs is not None
    return api_jobs


@strawberry.type
class Job:
    @strawberry.field
    def get_jobs(self) -> List[ApiJob]:
        return get_all_jobs()

    @strawberry.field
    def get_job(self, job_id: str) -> Optional[ApiJob]:
        return get_api_job_by_id(job_id)
