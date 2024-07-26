"""Services mutations"""

# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.jobs import JobStatus

from traceback import format_tb as format_traceback

from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)
from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)

from selfprivacy_api.actions.services import (
    move_service,
    ServiceNotFoundError,
    VolumeNotFoundError,
)

from selfprivacy_api.services import get_service_by_id


@strawberry.type
class ServiceMutationReturn(GenericMutationReturn):
    """Service mutation return type."""

    service: typing.Optional[Service] = None


@strawberry.input
class SetServiceConfigurationInput:
    """Set service configuration input type.
    The values might be of different types: str or bool.
    """

    service_id: str
    configuration: strawberry.scalars.JSON
    """Yes, it is a JSON scalar, which is supposed to be a Map<str, Union[str, int, bool]>.
    I can't define it as a proper type because GraphQL doesn't support unions in input types.
    There is a @oneOf directive, but it doesn't fit this usecase.

    Other option would have been doing something like this:
    ```python
    @strawberry.type
    class StringConfigurationInputField:
        fieldId: str
        value: str

    @strawberry.type
    class BoolConfigurationInputField:
        fieldId: str
        value: bool

    // ...

    @strawberry.input
    class SetServiceConfigurationInput:
        service_id: str
        stringFields: List[StringConfigurationInputField]
        boolFields: List[BoolConfigurationInputField]
        enumFields: List[EnumConfigurationInputField]
        intFields: List[IntConfigurationInputField]
    ```

    But it would be very painful to maintain and will break compatibility with
    every change.

    Be careful when parsing it. Probably it will be wise to add a parser/validator
    later when we get a new Pydantic integration in Strawberry.

    -- Inex, 26.07.2024
    """


@strawberry.input
class MoveServiceInput:
    """Move service input type."""

    service_id: str
    location: str


@strawberry.type
class ServiceJobMutationReturn(GenericJobMutationReturn):
    """Service job mutation return type."""

    service: typing.Optional[Service] = None


@strawberry.type
class ServicesMutations:
    """Services mutations."""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def enable_service(self, service_id: str) -> ServiceMutationReturn:
        """Enable service."""
        try:
            service = get_service_by_id(service_id)
            if service is None:
                return ServiceMutationReturn(
                    success=False,
                    message="Service not found.",
                    code=404,
                )
            service.enable()
        except Exception as e:
            return ServiceMutationReturn(
                success=False,
                message=pretty_error(e),
                code=400,
            )

        return ServiceMutationReturn(
            success=True,
            message="Service enabled.",
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def disable_service(self, service_id: str) -> ServiceMutationReturn:
        """Disable service."""
        try:
            service = get_service_by_id(service_id)
            if service is None:
                return ServiceMutationReturn(
                    success=False,
                    message="Service not found.",
                    code=404,
                )
            service.disable()
        except Exception as e:
            return ServiceMutationReturn(
                success=False,
                message=pretty_error(e),
                code=400,
            )
        return ServiceMutationReturn(
            success=True,
            message="Service disabled.",
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def stop_service(self, service_id: str) -> ServiceMutationReturn:
        """Stop service."""
        service = get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message="Service not found.",
                code=404,
            )
        service.stop()
        return ServiceMutationReturn(
            success=True,
            message="Service stopped.",
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def start_service(self, service_id: str) -> ServiceMutationReturn:
        """Start service."""
        service = get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message="Service not found.",
                code=404,
            )
        service.start()
        return ServiceMutationReturn(
            success=True,
            message="Service started.",
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def restart_service(self, service_id: str) -> ServiceMutationReturn:
        """Restart service."""
        service = get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message="Service not found.",
                code=404,
            )
        service.restart()
        return ServiceMutationReturn(
            success=True,
            message="Service restarted.",
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_service_configuration(
        self, input: SetServiceConfigurationInput
    ) -> ServiceMutationReturn:
        """Set the new configuration values"""
        service = get_service_by_id(input.service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message=f"Service does not exist: {input.service_id}",
                code=404,
            )
        try:
            service.set_configuration(input.configuration)
            return ServiceMutationReturn(
                success=True,
                message="Service configuration updated.",
                code=200,
                service=service_to_graphql_service(service),
            )
        except ValueError as e:
            return ServiceMutationReturn(
                success=False,
                message=e.args[0],
                code=400,
                service=service_to_graphql_service(service),
            )
        except Exception as e:
            return ServiceMutationReturn(
                success=False,
                message=pretty_error(e),
                code=400,
                service=service_to_graphql_service(service),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def move_service(self, input: MoveServiceInput) -> ServiceJobMutationReturn:
        """Move service."""
        # We need a service instance for a reply later
        service = get_service_by_id(input.service_id)
        if service is None:
            return ServiceJobMutationReturn(
                success=False,
                message=f"Service does not exist: {input.service_id}",
                code=404,
            )

        try:
            job = move_service(input.service_id, input.location)

        except (ServiceNotFoundError, VolumeNotFoundError) as e:
            return ServiceJobMutationReturn(
                success=False,
                message=pretty_error(e),
                code=404,
            )
        except Exception as e:
            return ServiceJobMutationReturn(
                success=False,
                message=pretty_error(e),
                code=400,
                service=service_to_graphql_service(service),
            )

        if job.status in [JobStatus.CREATED, JobStatus.RUNNING]:
            return ServiceJobMutationReturn(
                success=True,
                message="Started moving the service.",
                code=200,
                service=service_to_graphql_service(service),
                job=job_to_api_job(job),
            )
        elif job.status == JobStatus.FINISHED:
            return ServiceJobMutationReturn(
                success=True,
                message="Service moved.",
                code=200,
                service=service_to_graphql_service(service),
                job=job_to_api_job(job),
            )
        else:
            return ServiceJobMutationReturn(
                success=False,
                message=f"While moving service and performing the step '{job.status_text}', error occured: {job.error}",
                code=400,
                service=service_to_graphql_service(service),
                job=job_to_api_job(job),
            )


def pretty_error(e: Exception) -> str:
    traceback = "/r".join(format_traceback(e.__traceback__))
    return type(e).__name__ + ": " + str(e) + ": " + traceback
