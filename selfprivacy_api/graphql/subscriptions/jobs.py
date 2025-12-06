# pylint: disable=too-few-public-methods

from typing import AsyncGenerator, List

from selfprivacy_api.jobs import job_notifications

from selfprivacy_api.graphql.common_types.jobs import ApiJob
from selfprivacy_api.graphql.queries.jobs import get_all_jobs

from selfprivacy_api.utils.localization import translate_job


async def job_updates(locale: str) -> AsyncGenerator[List[ApiJob], None]:
    # Send the complete list of jobs every time anything gets updated
    async for _ in job_notifications():
        jobs = await get_all_jobs()
        yield [translate_job(job=j, locale=locale) for j in jobs]
