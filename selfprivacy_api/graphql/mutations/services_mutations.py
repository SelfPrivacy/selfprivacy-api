"""Services mutations"""

# pylint: disable=too-few-public-methods
import gettext
from typing import Optional

import strawberry
from opentelemetry import trace
from strawberry.types import Info

from selfprivacy_api.actions.services import (
    move_service,
)
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job, translate_job
from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)
from selfprivacy_api.jobs import JobStatus
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.utils import pretty_error
from selfprivacy_api.utils.localization import (
    TranslateSystemMessage as t,
    get_locale,
)

tracer = trace.get_tracer(__name__)


_ = gettext.gettext

SERVICE_NOT_FOUND = _("Service not found")


@strawberry.type
class ServiceMutationReturn(GenericMutationReturn):
    """Service mutation return type."""

    service: Optional[Service] = None


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

    service: Optional[Service] = None


@strawberry.type
class ServicesMutations:
    """Services mutations."""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def enable_service(
        self, info: Info, service_id: str
    ) -> ServiceMutationReturn:
        """Enable service."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "enable_service_mutation", attributes={"service_id": service_id}
        ):
            try:
                service = await ServiceManager.get_service_by_id(service_id)
                if service is None:
                    return ServiceMutationReturn(
                        success=False,
                        message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
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
                message=t.translate(text=_("Service enabled."), locale=locale),
                code=200,
                service=await service_to_graphql_service(service),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def disable_service(
        self, info: Info, service_id: str
    ) -> ServiceMutationReturn:
        """Disable service."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "disable_service_mutation", attributes={"service_id": service_id}
        ):
            try:
                service = await ServiceManager.get_service_by_id(service_id)
                if service is None:
                    return ServiceMutationReturn(
                        success=False,
                        message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
                        code=404,
                    )
                service.disable()
            except Exception as error:
                return ServiceMutationReturn(
                    success=False,
                    message=pretty_error(error),
                    code=400,
                )
            return ServiceMutationReturn(
                success=True,
                message=t.translate(text=_("Service disabled."), locale=locale),
                code=200,
                service=await service_to_graphql_service(service),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def stop_service(self, info: Info, service_id: str) -> ServiceMutationReturn:
        """Stop service."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "stop_service_mutation", attributes={"service_id": service_id}
        ):
            service = await ServiceManager.get_service_by_id(service_id)
            if service is None:
                return ServiceMutationReturn(
                    success=False,
                    message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
                    code=404,
                )
            await service.stop()
            return ServiceMutationReturn(
                success=True,
                message=t.translate(text=_("Service stopped."), locale=locale),
                code=200,
                service=await service_to_graphql_service(service),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def start_service(self, info: Info, service_id: str) -> ServiceMutationReturn:
        """Start service."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "start_service_mutation", attributes={"service_id": service_id}
        ):
            service = await ServiceManager.get_service_by_id(service_id)
            if service is None:
                return ServiceMutationReturn(
                    success=False,
                    message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
                    code=404,
                )
            await service.start()
            return ServiceMutationReturn(
                success=True,
                message=t.translate(text=_("Service started."), locale=locale),
                code=200,
                service=await service_to_graphql_service(service),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def restart_service(
        self, info: Info, service_id: str
    ) -> ServiceMutationReturn:
        """Restart service."""
        with tracer.start_as_current_span(
            "restart_service_mutation", attributes={"service_id": service_id}
        ):
            locale = get_locale(info=info)

            service = await ServiceManager.get_service_by_id(service_id)
            if service is None:
                return ServiceMutationReturn(
                    success=False,
                    message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
                    code=404,
                )
            await service.restart()
            return ServiceMutationReturn(
                success=True,
                message=t.translate(text=_("Service restarted."), locale=locale),
                code=200,
                service=await service_to_graphql_service(service),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def set_service_configuration(
        self, info: Info, input: SetServiceConfigurationInput
    ) -> ServiceMutationReturn:
        """Set the new configuration values"""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "set_service_configuration_mutation",
            attributes={
                "service_id": input.service_id,
            },
        ):
            service = await ServiceManager.get_service_by_id(input.service_id)
            if service is None:
                return ServiceMutationReturn(
                    success=False,
                    message=t.translate(
                        text=_("Service does not exist: %(service_id)s"),
                        locale=locale,
                    )
                    % {"service_id": input.service_id},
                    code=404,
                )
            try:
                service.set_configuration(input.configuration)
            except ValueError as error:
                return ServiceMutationReturn(
                    success=False,
                    message=error.args[0],
                    code=400,
                    service=await service_to_graphql_service(service),
                )
            except Exception as error:
                return ServiceMutationReturn(
                    success=False,
                    message=pretty_error(error),
                    code=400,
                    service=await service_to_graphql_service(service),
                )
            return ServiceMutationReturn(
                success=True,
                message=t.translate(
                    text=_("Service configuration updated."), locale=locale
                ),
                code=200,
                service=await service_to_graphql_service(service),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def move_service(
        self, info: Info, input: MoveServiceInput
    ) -> ServiceJobMutationReturn:
        """Move service."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "move_service_mutation",
            attributes={
                "service_id": input.service_id,
                "location": input.location,
            },
        ):
            # We need a service instance for a reply later
            service = await ServiceManager.get_service_by_id(input.service_id)
            if service is None:
                return ServiceJobMutationReturn(
                    success=False,
                    message=t.translate(
                        text=_("Service does not exist: %(service_id)s"),
                        locale=locale,
                    )
                    % {"service_id": input.service_id},
                    code=404,
                )

            try:
                job = await move_service(input.service_id, input.location)
            except Exception as error:
                if isinstance(error, AbstractException):
                    return ServiceJobMutationReturn(
                        success=False,
                        message=error.get_error_message(locale=locale),
                        code=error.code,
                    )
                else:
                    return ServiceJobMutationReturn(
                        success=False,
                        message=pretty_error(error),
                        code=400,
                        service=await service_to_graphql_service(service),
                    )

            if job.status in [JobStatus.CREATED, JobStatus.RUNNING]:
                return ServiceJobMutationReturn(
                    success=True,
                    message=t.translate(
                        text=_("Started moving the service."), locale=locale
                    ),
                    code=200,
                    service=await service_to_graphql_service(service),
                    job=translate_job(job=job_to_api_job(job), locale=locale),
                )
            elif job.status == JobStatus.FINISHED:
                return ServiceJobMutationReturn(
                    success=True,
                    message=t.translate(text=_("Service moved."), locale=locale),
                    code=200,
                    service=await service_to_graphql_service(service),
                    job=translate_job(job=job_to_api_job(job), locale=locale),
                )
            else:
                return ServiceJobMutationReturn(
                    success=False,
                    message=t.translate(
                        text=_(
                            "While moving service and performing the step '%(status_text)s', an error occurred: %(error)s"
                        ),
                        locale=locale,
                    )
                    % {
                        "status_text": job.status_text,
                        "error": job.error,
                    },
                    code=400,
                    service=await service_to_graphql_service(service),
                    job=translate_job(job=job_to_api_job(job), locale=locale),
                )
