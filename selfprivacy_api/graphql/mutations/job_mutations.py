"""Manipulate jobs"""

# pylint: disable=too-few-public-methods

import gettext

import strawberry
from strawberry.types import Info
from opentelemetry import trace

from selfprivacy_api.graphql.mutations.mutation_interface import GenericMutationReturn
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.jobs import Jobs
from selfprivacy_api.utils.localization import TranslateSystemMessage as t


_ = gettext.gettext

tracer = trace.get_tracer(__name__)


@strawberry.type
class JobMutations:
    """Mutations related to jobs"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_job(self, job_id: str, info: Info) -> GenericMutationReturn:
        """Remove a job from the queue"""
        locale = info.context["locale"]

        with tracer.start_as_current_span(
            "remove_job_mutation",
            attributes={
                "job_id": job_id,
            },
        ):
            result = Jobs.remove_by_uid(job_id)
            if result:
                return GenericMutationReturn(
                    success=True,
                    code=200,
                    message=t.translate(text=_("Job removed"), locale=locale),
                )
            return GenericMutationReturn(
                success=False,
                code=404,
                message=t.translate(text=_("Job not found"), locale=locale),
            )
