"""System management mutations"""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    MutationReturnInterface,
)

import selfprivacy_api.actions.system as system_actions


@strawberry.type
class TimezoneMutationReturn(MutationReturnInterface):
    """Return type of the timezone mutation, contains timezone"""

    timezone: typing.Optional[str]


@strawberry.type
class AutoUpgradeSettingsMutationReturn(MutationReturnInterface):
    """Return type autoUpgrade Settings"""

    enableAutoUpgrade: bool
    allowReboot: bool


@strawberry.input
class AutoUpgradeSettingsInput:
    """Input type for auto upgrade settings"""

    enableAutoUpgrade: typing.Optional[bool] = None
    allowReboot: typing.Optional[bool] = None


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
    def run_system_rebuild(self) -> GenericMutationReturn:
        system_actions.rebuild_system()
        return GenericMutationReturn(
            success=True,
            message="Starting rebuild system",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_rollback(self) -> GenericMutationReturn:
        system_actions.rollback_system()
        return GenericMutationReturn(
            success=True,
            message="Starting rebuild system",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_upgrade(self) -> GenericMutationReturn:
        system_actions.upgrade_system()
        return GenericMutationReturn(
            success=True,
            message="Starting rebuild system",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def reboot_system(self) -> GenericMutationReturn:
        system_actions.reboot_system()
        return GenericMutationReturn(
            success=True,
            message="System reboot has started",
            code=200,
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
