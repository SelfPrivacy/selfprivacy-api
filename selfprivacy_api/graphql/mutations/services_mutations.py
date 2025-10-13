"""Services mutations"""

# pylint: disable=too-few-public-methods
import gettext
from typing import Optional

import strawberry
from strawberry.types import Info

from selfprivacy_api.utils import pretty_error
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.jobs import JobStatus


from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)
from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)
from selfprivacy_api.graphql.queries.jobs import translate_job

from selfprivacy_api.actions.services import (
    move_service,
    ServiceNotFoundError,
    VolumeNotFoundError,
)

from selfprivacy_api.services import ServiceManager


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
    def enable_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Enable service."""

        locale = info.context["locale"]
        try:
            service = ServiceManager.get_service_by_id(service_id)
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
            message=_("Service enabled."),
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def disable_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Disable service."""

        locale = info.context["locale"]
        try:
            service = ServiceManager.get_service_by_id(service_id)
            if service is None:
                return ServiceMutationReturn(
                    success=False,
                    message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
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
            message=_("Service disabled."),
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def stop_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Stop service."""

        locale = info.context["locale"]
        service = ServiceManager.get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
                code=404,
            )
        service.stop()
        return ServiceMutationReturn(
            success=True,
            message=_("Service stopped."),
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def start_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Start service."""

        locale = info.context["locale"]
        service = ServiceManager.get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
                code=404,
            )
        service.start()
        return ServiceMutationReturn(
            success=True,
            message=t.translate(text=_("Service started."), locale=locale),
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def restart_service(self, service_id: str, info: Info) -> ServiceMutationReturn:
        """Restart service."""

        locale = info.context["locale"]
        service = ServiceManager.get_service_by_id(service_id)
        if service is None:
            return ServiceMutationReturn(
                success=False,
                message=t.translate(text=SERVICE_NOT_FOUND, locale=locale),
                code=404,
            )
        service.restart()
        return ServiceMutationReturn(
            success=True,
            message=t.translate(text=_("Service restarted."), locale=locale),
            code=200,
            service=service_to_graphql_service(service),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_service_configuration(
        self, input: SetServiceConfigurationInput, info: Info
    ) -> ServiceMutationReturn:
        """Set the new configuration values"""

        locale = info.context["locale"]
        service = ServiceManager.get_service_by_id(input.service_id)
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
            return ServiceMutationReturn(
                success=True,
                message=t.translate(
                    text=_("Service configuration updated."), locale=locale
                ),
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
    def move_service(
        self, input: MoveServiceInput, info: Info
    ) -> ServiceJobMutationReturn:
        """Move service."""
        # We need a service instance for a reply later
        locale = info.context["locale"]
        service = ServiceManager.get_service_by_id(input.service_id)
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
            job = move_service(input.service_id, input.location)

        except (ServiceNotFoundError, VolumeNotFoundError) as error:
            return ServiceJobMutationReturn(
                success=False,
                message=error.get_error_message(locale=locale),
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
                message=t.translate(
                    text=_("Started moving the service."), locale=locale
                ),
                code=200,
                service=service_to_graphql_service(service),
                job=translate_job(job=job_to_api_job(job), locale=locale),
            )
        elif job.status == JobStatus.FINISHED:
            return ServiceJobMutationReturn(
                success=True,
                message=t.translate(text=_("Service moved."), locale=locale),
                code=200,
                service=service_to_graphql_service(service),
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
                service=service_to_graphql_service(service),
                job=translate_job(job=job_to_api_job(job), locale=locale),
            )
