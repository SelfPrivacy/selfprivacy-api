import asyncio
import datetime
from typing import AsyncGenerator
import typing

import strawberry
from selfprivacy_api.graphql import IsAuthenticated

from selfprivacy_api.jobs import Job, Jobs


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
class JobSubscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)

    @strawberry.subscription()
    async def job_subscription(self) -> AsyncGenerator[typing.List[ApiJob], None]:
        is_updated = True

        def callback(jobs: typing.List[Job]):
            nonlocal is_updated
            is_updated = True

        print("Subscribing to job updates...")
        Jobs.get_instance().add_observer(callback)
        yield [
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
        while True:
            if is_updated:
                is_updated = False
                yield [
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
