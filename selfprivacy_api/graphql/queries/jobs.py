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
    Jobs.get_jobs()

    return [job_to_api_job(job) for job in Jobs.get_jobs()]


@strawberry.type
class Job:
    @strawberry.field
    def get_jobs(self) -> List[ApiJob]:
        return get_all_jobs()

    @strawberry.field
    def get_job(self, job_id: str) -> Optional[ApiJob]:
        return get_api_job_by_id(job_id)
