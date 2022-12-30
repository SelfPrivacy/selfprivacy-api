"""Jobs status"""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql.common_types.jobs import (
    ApiJob,
    get_api_job_by_id,
    job_to_api_job,
)

from selfprivacy_api.jobs import Jobs


@strawberry.type
class Job:
    @strawberry.field
    def get_jobs(self) -> typing.List[ApiJob]:

        Jobs.get_jobs()

        return [job_to_api_job(job) for job in Jobs.get_jobs()]

    @strawberry.field
    def get_job(self, job_id: str) -> typing.Optional[ApiJob]:
        return get_api_job_by_id(job_id)
