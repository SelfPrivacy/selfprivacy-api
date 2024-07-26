"""Manipulate jobs"""

# pylint: disable=too-few-public-methods
import strawberry

from selfprivacy_api.graphql.mutations.mutation_interface import GenericMutationReturn
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.jobs import Jobs


@strawberry.type
class JobMutations:
    """Mutations related to jobs"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_job(self, job_id: str) -> GenericMutationReturn:
        """Remove a job from the queue"""
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
