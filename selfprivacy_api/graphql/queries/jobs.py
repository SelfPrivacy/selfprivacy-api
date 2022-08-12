"""Jobs status"""
# pylint: disable=too-few-public-methods
import typing
import strawberry
import datetime

from selfprivacy_api.jobs import Jobs


@strawberry.type
class ApiJob:
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


@strawberry.type
class Job:
    @strawberry.field
    def get_jobs(self) -> typing.List[ApiJob]:

        Jobs.get_instance().get_jobs()

        return [
            ApiJob(
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
            for job in Jobs.get_instance().get_jobs()
        ]
