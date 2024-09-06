from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
)


def api_job_mutation_error(error: Exception, code: int = 400):
    return GenericJobMutationReturn(
        success=False,
        code=code,
        message=str(error),
        job=None,
    )
