"""System management mutations"""

# pylint: disable=too-few-public-methods

from typing import Optional
import gettext

import strawberry
from opentelemetry import trace
from strawberry.types import Info

from selfprivacy_api.utils import pretty_error
from selfprivacy_api.utils.localization import (
    TranslateSystemMessage as t,
    get_locale,
)
from selfprivacy_api.jobs.nix_collect_garbage import start_nix_collect_garbage

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.graphql.queries.providers import DnsProvider
from selfprivacy_api.graphql.common_types.jobs import translate_job
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
    MutationReturnInterface,
)

import selfprivacy_api.actions.system as system_actions
import selfprivacy_api.actions.ssh as ssh_actions
from selfprivacy_api.actions.system import set_dns_provider

tracer = trace.get_tracer(__name__)
_ = gettext.gettext


@strawberry.type
class TimezoneMutationReturn(MutationReturnInterface):
    """Return type of the timezone mutation, contains timezone"""

    timezone: Optional[str]


@strawberry.type
class AutoUpgradeSettingsMutationReturn(MutationReturnInterface):
    """Return type autoUpgrade Settings"""

    enableAutoUpgrade: bool
    allowReboot: bool


@strawberry.type
class SSHSettingsMutationReturn(MutationReturnInterface):
    """A return type for after changing SSH settings"""

    enable: bool
    password_authentication: bool


@strawberry.input
class SSHSettingsInput:
    """Input type for SSH settings"""

    enable: bool
    password_authentication: Optional[bool] = None


@strawberry.input
class SetDnsProviderInput:
    """Input type to set the provider"""

    provider: DnsProvider
    api_token: str


@strawberry.input
class AutoUpgradeSettingsInput:
    """Input type for auto upgrade settings"""

    enableAutoUpgrade: Optional[bool] = None
    allowReboot: Optional[bool] = None


@strawberry.type
class SystemMutations:
    """Mutations related to system settings"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def change_timezone(self, timezone: str, info: Info) -> TimezoneMutationReturn:
        """Change the timezone of the server. Timezone is a tzdatabase name."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "change_timezone_mutation",
            attributes={
                "timezone": timezone,
            },
        ):
            try:
                system_actions.change_timezone(timezone)
            except system_actions.InvalidTimezone as e:
                return TimezoneMutationReturn(
                    success=False,
                    message=str(e),
                    code=400,
                    timezone=None,
                )
            return TimezoneMutationReturn(
                success=True,
                message=t.translate(text=_("Timezone changed"), locale=locale),
                code=200,
                timezone=timezone,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def change_auto_upgrade_settings(
        self, settings: AutoUpgradeSettingsInput, info: Info
    ) -> AutoUpgradeSettingsMutationReturn:
        """Change auto upgrade settings of the server."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "change_auto_upgrade_settings_mutation",
            attributes={
                "enableAutoUpgrade": str(settings.enableAutoUpgrade),
                "allowReboot": str(settings.allowReboot),
            },
        ):
            system_actions.set_auto_upgrade_settings(
                settings.enableAutoUpgrade, settings.allowReboot
            )

            new_settings = system_actions.get_auto_upgrade_settings()

            return AutoUpgradeSettingsMutationReturn(
                success=True,
                message=t.translate(
                    text=_("Auto-upgrade settings changed"), locale=locale
                ),
                code=200,
                enableAutoUpgrade=new_settings.enable,
                allowReboot=new_settings.allowReboot,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def change_ssh_settings(
        self, settings: SSHSettingsInput, info: Info
    ) -> SSHSettingsMutationReturn:
        """Change ssh settings of the server."""
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "change_ssh_settings_mutation",
            attributes={
                "enable": str(settings.enable),
                "password_authentication": str(settings.password_authentication),
            },
        ):
            ssh_actions.set_ssh_settings(
                enable=settings.enable,
            )

            new_settings = ssh_actions.get_ssh_settings()

            return SSHSettingsMutationReturn(
                success=True,
                message=t.translate(text=_("SSH settings changed"), locale=locale),
                code=200,
                enable=new_settings.enable,
                password_authentication=new_settings.passwordAuthentication,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_rebuild(self, info: Info) -> GenericJobMutationReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span("run_system_rebuild"):
            try:
                job = system_actions.rebuild_system()
                return GenericJobMutationReturn(
                    success=True,
                    message=t.translate(
                        text=_("Starting system rebuild"), locale=locale
                    ),
                    code=200,
                    job=translate_job(job=job_to_api_job(job), locale=locale),
                )
            except system_actions.ShellException as error:
                return GenericJobMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=500,
                )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def run_system_rollback(self, info: Info) -> GenericMutationReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span("run_system_rollback"):
            try:
                await system_actions.rollback_system()
                return GenericMutationReturn(
                    success=True,
                    message="Starting system rollback",
                    code=200,
                )
            except system_actions.ShellException as error:
                return GenericMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=500,
                )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_upgrade(self, info: Info) -> GenericJobMutationReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span("run_system_upgrade"):
            try:
                job = system_actions.upgrade_system()
                return GenericJobMutationReturn(
                    success=True,
                    message=t.translate(
                        text=_("Starting system upgrade"), locale=locale
                    ),
                    code=200,
                    job=translate_job(job=job_to_api_job(job), locale=locale),
                )
            except system_actions.ShellException as error:
                return GenericJobMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=500,
                )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def reboot_system(self, info: Info) -> GenericMutationReturn:
        locale = get_locale(info=info)

        await system_actions.reboot_system()
        try:
            return GenericMutationReturn(
                success=True,
                message=t.translate(text=_("System reboot has started"), locale=locale),
                code=200,
            )
        except system_actions.ShellException as error:
            return GenericMutationReturn(
                success=False,
                message=error.get_error_message(locale=locale),
                code=500,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def pull_repository_changes(self, info: Info) -> GenericMutationReturn:
        locale = get_locale(info=info)
        return GenericMutationReturn(
            success=False,
            message=t.translate(
                text=_("There is no repository to pull changes from."), locale=locale
            ),
            code=400,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def nix_collect_garbage(self, info: Info) -> GenericJobMutationReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span("nix_collect_garbage_mutation"):
            job = start_nix_collect_garbage()

            return GenericJobMutationReturn(
                success=True,
                code=200,
                message=t.translate(
                    text=_("Garbage collector started..."), locale=locale
                ),
                job=translate_job(job=job_to_api_job(job), locale=locale),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_dns_provider(
        self, input: SetDnsProviderInput, info: Info
    ) -> GenericMutationReturn:
        locale = get_locale(info=info)

        with tracer.start_as_current_span(
            "set_dns_provider_mutation",
            attributes={
                "provider": input.provider.value,
            },
        ):
            try:
                set_dns_provider(input.provider, input.api_token)
                return GenericMutationReturn(
                    success=True,
                    code=200,
                    message=t.translate(text=_("Provider set"), locale=locale),
                )
            except Exception as e:
                return GenericMutationReturn(
                    success=False,
                    code=400,
                    message=pretty_error(e),
                )
