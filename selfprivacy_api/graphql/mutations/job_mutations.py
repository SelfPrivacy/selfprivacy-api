"""Manipulate jobs"""

# pylint: disable=too-few-public-methods
import strawberry
from opentelemetry import trace

from selfprivacy_api.graphql.mutations.mutation_interface import GenericMutationReturn
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.jobs import Jobs

tracer = trace.get_tracer(__name__)


@strawberry.type
class JobMutations:
    """Mutations related to jobs"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_job(self, job_id: str) -> GenericMutationReturn:
        """Remove a job from the queue"""
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
                    message="Job removed",
                )
            return GenericMutationReturn(
                success=False,
                code=404,
                message="Job not found",
            )
