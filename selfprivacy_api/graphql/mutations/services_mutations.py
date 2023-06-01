"""Services mutations"""
# pylint: disable=too-few-public-methods
from threading import local
import typing
import strawberry
from strawberry.types import Info
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job

from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobButationReturn,
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
class ServiceJobMutationReturn(GenericJobButationReturn):
    """Service job mutation return type."""

    service: typing.Optional[Service] = None


@strawberry.type
class ServicesMutations:
    """Services mutations."""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def enable_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Enable service."""
        locale = info.context["locale"]
        service = get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message="Service not found.",
                code=404,
            )
        service.enable()
        return ServiceMutationReturn(
            success=True,
            message="Service enabled.",
            code=200,
            service=service_to_graphql_service(service, locale),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def disable_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Disable service."""
        locale = info.context["locale"]
        service = get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message="Service not found.",
                code=404,
            )
        service.disable()
        return ServiceMutationReturn(
            success=True,
            message="Service disabled.",
            code=200,
            service=service_to_graphql_service(service, locale),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def stop_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Stop service."""
        locale = info.context["locale"]
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
            service=service_to_graphql_service(service, locale),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def start_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Start service."""
        locale = info.context["locale"]
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
            service=service_to_graphql_service(service, locale),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def restart_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Restart service."""
        locale = info.context["locale"]
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
            service=service_to_graphql_service(service, locale),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def move_service(
        self, input: MoveServiceInput, info: Info
    ) -> ServiceJobMutationReturn:
        """Move service."""
        locale = info.context["locale"]
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
                service=service_to_graphql_service(service, locale),
            )
        volume = BlockDevices().get_block_device(input.location)
        if volume is None:
            return ServiceJobMutationReturn(
                success=False,
                message="Volume not found.",
                code=404,
                service=service_to_graphql_service(service, locale),
            )
        job = service.move_to_volume(volume)
        return ServiceJobMutationReturn(
            success=True,
            message="Service moved.",
            code=200,
            service=service_to_graphql_service(service, locale),
            job=job_to_api_job(job),
        )
