"""Services mutations"""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.jobs import JobStatus

from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)

from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.utils.block_devices import BlockDevices


@strawberry.type
class ServiceMutationReturn(GenericMutationReturn):
    """Service mutation return type."""

    service: typing.Optional[Service] = None


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
                message=format_error(e),
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
                message=format_error(e),
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
    def move_service(self, input: MoveServiceInput) -> ServiceJobMutationReturn:
        """Move service."""
        service = get_service_by_id(input.service_id)
        if service is None:
            return ServiceJobMutationReturn(
                success=False,
                message="Service not found.",
                code=404,
            )
        if not service.is_movable():
            return ServiceJobMutationReturn(
                success=False,
                message="Service is not movable.",
                code=400,
                service=service_to_graphql_service(service),
            )
        volume = BlockDevices().get_block_device(input.location)
        if volume is None:
            return ServiceJobMutationReturn(
                success=False,
                message="Volume not found.",
                code=404,
                service=service_to_graphql_service(service),
            )
        job = service.move_to_volume(volume)
        if job.status == JobStatus.FINISHED:
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
                message=f"Service move failure: {job.status_text}",
                code=400,
                service=service_to_graphql_service(service),
                job=job_to_api_job(job),
            )


def format_error(e: Exception) -> str:
    return type(e).__name__ + ": " + str(e)
