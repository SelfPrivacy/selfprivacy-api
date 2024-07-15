# pylint: disable=too-few-public-methods

from typing import AsyncGenerator, List

from selfprivacy_api.jobs import job_notifications

from selfprivacy_api.graphql.common_types.jobs import ApiJob
from selfprivacy_api.graphql.queries.jobs import get_all_jobs


async def job_updates() -> AsyncGenerator[List[ApiJob], None]:
    # Send the complete list of jobs every time anything gets updated
    async for notification in job_notifications():
        yield get_all_jobs()
