from typing import Any

from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)
from selfprivacy_api.utils import pretty_error


def api_job_mutation_error(error: Exception, code: int = 400):
    return GenericJobMutationReturn(
        success=False,
        code=code,
        message=str(error),
        job=None,
    )


def mutation_error_fields(error: Exception, locale: str, code: int) -> dict[str, Any]:
    if isinstance(error, AbstractException):
        return {
            "success": False,
            "message": error.get_error_message(locale=locale),
            "code": error.code,
        }
    return {
        "success": False,
        "message": pretty_error(error),
        "code": code,
    }


def generic_mutation_error(
    error: Exception, locale: str, code: int
) -> GenericMutationReturn:
    return GenericMutationReturn(**mutation_error_fields(error, locale, code))


def generic_job_mutation_error(
    error: Exception, locale: str, code: int
) -> GenericJobMutationReturn:
    return GenericJobMutationReturn(**mutation_error_fields(error, locale, code))
