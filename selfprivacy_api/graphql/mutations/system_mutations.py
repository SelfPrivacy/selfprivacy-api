"""System management mutations"""
# pylint: disable=too-few-public-methods
import subprocess
import typing
import pytz
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
    MutationReturnInterface,
)
from selfprivacy_api.utils import WriteUserData


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
        if timezone not in pytz.all_timezones:
            return TimezoneMutationReturn(
                success=False,
                message="Invalid timezone",
                code=400,
                timezone=None,
            )
        with WriteUserData() as data:
            data["timezone"] = timezone
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
        with WriteUserData() as data:
            if "autoUpgrade" not in data:
                data["autoUpgrade"] = {}
            if "enable" not in data["autoUpgrade"]:
                data["autoUpgrade"]["enable"] = True
            if "allowReboot" not in data["autoUpgrade"]:
                data["autoUpgrade"]["allowReboot"] = False

            if settings.enableAutoUpgrade is not None:
                data["autoUpgrade"]["enable"] = settings.enableAutoUpgrade
            if settings.allowReboot is not None:
                data["autoUpgrade"]["allowReboot"] = settings.allowReboot

            auto_upgrade = data["autoUpgrade"]["enable"]
            allow_reboot = data["autoUpgrade"]["allowReboot"]

        return AutoUpgradeSettingsMutationReturn(
            success=True,
            message="Auto-upgrade settings changed",
            code=200,
            enableAutoUpgrade=auto_upgrade,
            allowReboot=allow_reboot,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_rebuild(self) -> GenericMutationReturn:
        rebuild_result = subprocess.Popen(
            ["systemctl", "start", "sp-nixos-rebuild.service"], start_new_session=True
        )
        rebuild_result.communicate()[0]
        return GenericMutationReturn(
            success=True,
            message="Starting rebuild system",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_rollback(self) -> GenericMutationReturn:
        rollback_result = subprocess.Popen(
            ["systemctl", "start", "sp-nixos-rollback.service"], start_new_session=True
        )
        rollback_result.communicate()[0]
        return GenericMutationReturn(
            success=True,
            message="Starting rebuild system",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def run_system_upgrade(self) -> GenericMutationReturn:
        upgrade_result = subprocess.Popen(
            ["systemctl", "start", "sp-nixos-upgrade.service"], start_new_session=True
        )
        upgrade_result.communicate()[0]
        return GenericMutationReturn(
            success=True,
            message="Starting rebuild system",
            code=200,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def reboot_system(self) -> GenericMutationReturn:
        subprocess.Popen(["reboot"], start_new_session=True)
        return GenericMutationReturn(
            success=True,
            message="System reboot has started",
            code=200,
        )
