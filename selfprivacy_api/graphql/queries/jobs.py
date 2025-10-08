"""Jobs status"""

# pylint: disable=too-few-public-methods
import strawberry
from strawberry.types import Info

from typing import List, Optional

from selfprivacy_api.jobs import Jobs
from selfprivacy_api.graphql.common_types.jobs import (
    ApiJob,
    get_api_job_by_id,
    job_to_api_job,
)
from selfprivacy_api.utils.localization import TranslateSystemMessage as t


def translate_job(job: ApiJob, locale: str) -> ApiJob:
    def _tr_opt(text: Optional[str], locale: str) -> Optional[str]:
        return t.translate(text=text, locale=locale) if text is not None else None

    return ApiJob(
        uid=job.uid,
        type_id=job.type_id,
        name=t.translate(text=job.name, locale=locale),
        description=t.translate(text=job.description, locale=locale),
        status=t.translate(text=job.status, locale=locale),
        status_text=_tr_opt(job.status_text, locale),
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        finished_at=job.finished_at,
        error=_tr_opt(job.error, locale),
        result=_tr_opt(job.result, locale),
    )


def get_all_jobs() -> List[ApiJob]:
    jobs = Jobs.get_jobs()
    api_jobs = [job_to_api_job(job) for job in jobs]
    assert api_jobs is not None
    return api_jobs


@strawberry.type
class Job:
    @strawberry.field
    def get_jobs(self, info: Info) -> List[ApiJob]:
        locale = info.context["locale"]

        all_jobs = get_all_jobs()
        translated_jobs = []
        for job in all_jobs:
            translated_jobs.append(translate_job(job=job, locale=locale))
        return translated_jobs

    @strawberry.field
    def get_job(self, job_id: str, info: Info) -> Optional[ApiJob]:
        locale = info.context["locale"]

        job = get_api_job_by_id(job_id)
        if job:
            return translate_job(job=job, locale=locale)
