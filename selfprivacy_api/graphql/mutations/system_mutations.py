"""System management mutations"""
# pylint: disable=too-few-public-methods
import typing
import pytz
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
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
