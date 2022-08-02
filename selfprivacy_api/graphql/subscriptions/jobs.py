import asyncio
from typing import AsyncGenerator
import typing

import strawberry
from selfprivacy_api.graphql import IsAuthenticated

from selfprivacy_api.jobs import Job, Jobs

@strawberry.type
class JobSubscription:
    @strawberry.subscription(permission_classes=[IsAuthenticated])
    async def job_subscription(self) -> AsyncGenerator[typing.List[Job], None]:
        is_updated = True
        def callback(jobs: typing.List[Job]):
            nonlocal is_updated
            is_updated = True
        Jobs().add_observer(callback)
        try:
            while True:
                if is_updated:
                    is_updated = False
                    yield Jobs().jobs
        except GeneratorExit:
            Jobs().remove_observer(callback)
            return
