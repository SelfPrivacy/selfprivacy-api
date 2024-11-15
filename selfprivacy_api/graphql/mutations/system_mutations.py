"""System management mutations"""

# pylint: disable=too-few-public-methods
from typing import Optional
import strawberry

from selfprivacy_api.utils import pretty_error
from selfprivacy_api.jobs.nix_collect_garbage import start_nix_collect_garbage

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.graphql.queries.providers import DnsProvider

from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
    MutationReturnInterface,
)

import selfprivacy_api.actions.system as system_actions
import selfprivacy_api.actions.ssh as ssh_actions
from selfprivacy_api.actions.system import set_dns_provider


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
    password_authentication: bool


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
    def change_timezone(self, timezone: str) -> TimezoneMutationReturn:
        """Change the timezone of the server. Timezone is a tzdatabase name."""
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
            message="Timezone changed",
            code=200,
            timezone=timezone,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def change_auto_upgrade_settings(
        self, settings: AutoUpgradeSettingsInput
    ) -> AutoUpgradeSettingsMutationReturn:
        """Change auto upgrade settings of the server."""
        system_actions.set_auto_upgrade_settings(
            settings.enableAutoUpgrade, settings.allowReboot
        )

        new_settings = system_actions.get_auto_upgrade_settings()

        return AutoUpgradeSettingsMutationReturn(
            success=True,
            message="Auto-upgrade settings changed",
            code=200,
            enableAutoUpgrade=new_settings.enable,
            allowReboot=new_settings.allowReboot,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def change_ssh_settings(
        self, settings: SSHSettingsInput
    ) -> SSHSettingsMutationReturn:
        """Change ssh settings of the server."""
        ssh_actions.set_ssh_settings(
            enable=settings.enable,
            password_authentication=settings.password_authentication,
        )

        new_settings = ssh_actions.get_ssh_settings()

        return SSHSettingsMutationReturn(
            success=True,
            message="SSH settings changed",
            code=200,
            enable=new_settings.enable,
            password_authentication=new_settings.passwordAuthentication,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_rebuild(self) -> GenericJobMutationReturn:
        try:
            job = system_actions.rebuild_system()
            return GenericJobMutationReturn(
                success=True,
                message="Starting system rebuild",
                code=200,
                job=job_to_api_job(job),
            )
        except system_actions.ShellException as e:
            return GenericJobMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_rollback(self) -> GenericMutationReturn:
        system_actions.rollback_system()
        try:
            return GenericMutationReturn(
                success=True,
                message="Starting system rollback",
                code=200,
            )
        except system_actions.ShellException as e:
            return GenericMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_upgrade(self) -> GenericJobMutationReturn:
        try:
            job = system_actions.upgrade_system()
            return GenericJobMutationReturn(
                success=True,
                message="Starting system upgrade",
                code=200,
                job=job_to_api_job(job),
            )
        except system_actions.ShellException as e:
            return GenericJobMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def reboot_system(self) -> GenericMutationReturn:
        system_actions.reboot_system()
        try:
            return GenericMutationReturn(
                success=True,
                message="System reboot has started",
                code=200,
            )
        except system_actions.ShellException as e:
            return GenericMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def pull_repository_changes(self) -> GenericMutationReturn:
        result = system_actions.pull_repository_changes()
        if result.status == 0:
            return GenericMutationReturn(
                success=True,
                message="Repository changes pulled",
                code=200,
            )
        return GenericMutationReturn(
            success=False,
            message=f"Failed to pull repository changes:\n{result.data}",
            code=500,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def nix_collect_garbage(self) -> GenericJobMutationReturn:
        job = start_nix_collect_garbage()

        return GenericJobMutationReturn(
            success=True,
            code=200,
            message="Garbage collector started...",
            job=job_to_api_job(job),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_dns_provider(self, input: SetDnsProviderInput) -> GenericMutationReturn:

        try:
            set_dns_provider(input.provider, input.api_token)
            return GenericMutationReturn(
                success=True,
                code=200,
                message="Provider set",
            )
        except Exception as e:
            return GenericMutationReturn(
                success=False,
                code=400,
                message=pretty_error(e),
            )
