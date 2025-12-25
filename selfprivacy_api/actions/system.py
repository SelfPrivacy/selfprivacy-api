"""Actions to manage the system."""

import gettext
import logging
import subprocess
from textwrap import dedent
from typing import Any, Optional

import pytz
from pydantic import BaseModel

from selfprivacy_api.graphql.queries.providers import DnsProvider
from selfprivacy_api.jobs import Job, Jobs, JobStatus
from selfprivacy_api.jobs.upgrade_system import rebuild_system_task
from selfprivacy_api.models.exception import ApiException
from selfprivacy_api.utils import ReadUserData, UserDataFiles, WriteUserData
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)
from selfprivacy_api.utils.strings import REPORT_IT_TO_SUPPORT_CHATS
from selfprivacy_api.utils.systemd import start_unit, systemd_proxy

logger = logging.getLogger(__name__)

_ = gettext.gettext


def get_timezone() -> str:
    """Get the timezone of the server"""
    with ReadUserData() as user_data:
        if "timezone" in user_data:
            return user_data["timezone"]
        return "Etc/UTC"


class InvalidTimezone(ApiException):
    """Invalid timezone"""

    def __init__(self, timezone: str):
        self.timezone = timezone

        logging.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Invalid timezone: %(timezone)s
                    Timezone not in pytz.all_timezones.
                    List of available timezones:
                    https://data.iana.org/time-zones/data/zone.tab
                    """
                )
            )
            % {"timezone": self.timezone},
            locale=locale,
        )


def change_timezone(timezone: str) -> None:
    """Change the timezone of the server"""
    if timezone not in pytz.all_timezones:
        raise InvalidTimezone(timezone=timezone)
    with WriteUserData() as user_data:
        user_data["timezone"] = timezone


class UserDataAutoUpgradeSettings(BaseModel):
    """Settings for auto-upgrading user data"""

    enable: bool = True
    allowReboot: bool = False


def set_dns_provider(provider: DnsProvider, token: str):
    with WriteUserData() as user_data:
        if "dns" not in user_data.keys():
            user_data["dns"] = {}
        user_data["dns"]["provider"] = provider.value

    with WriteUserData(file_type=UserDataFiles.SECRETS) as secrets:
        if "dns" not in secrets.keys():
            secrets["dns"] = {}
        secrets["dns"]["apiKey"] = token


def get_auto_upgrade_settings() -> UserDataAutoUpgradeSettings:
    """Get the auto-upgrade settings"""
    with ReadUserData() as user_data:
        if "autoUpgrade" in user_data:
            return UserDataAutoUpgradeSettings(**user_data["autoUpgrade"])
        return UserDataAutoUpgradeSettings()


def set_auto_upgrade_settings(
    enable: Optional[bool] = None, allowReboot: Optional[bool] = None
) -> None:
    """Set the auto-upgrade settings"""
    with WriteUserData() as user_data:
        if "autoUpgrade" not in user_data:
            user_data["autoUpgrade"] = {}
        if enable is not None:
            user_data["autoUpgrade"]["enable"] = enable
        if allowReboot is not None:
            user_data["autoUpgrade"]["allowReboot"] = allowReboot


class ShellException(ApiException):
    """Shell command failed"""

    def __init__(self, command: str, output: Any, description: str):
        self.command = command
        self.description = description
        self.output = str(output)

        logging.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Shell command failed.
                    %(description)s
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    Executed command: %(command)s
                    Output: %(output)s
                    """
                )
            )
            % {
                "command": self.command,
                "description": self.description,
                "output": self.output,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            },
            locale=locale,
        )


def add_rebuild_job() -> Job:
    return Jobs.add(
        type_id="system.nixos.rebuild",
        name=_("Rebuild system"),
        description=_(
            "Applying the new system configuration by building the new NixOS generation."
        ),
        status=JobStatus.CREATED,
    )


def rebuild_system() -> Job:
    """Rebuild the system"""
    job = add_rebuild_job()
    rebuild_system_task(job)
    return job


async def rollback_system():
    """Rollback the system"""
    await start_unit("sp-nixos-rollback.service")


def upgrade_system() -> Job:
    """Upgrade the system"""
    job = Jobs.add(
        type_id="system.nixos.upgrade",
        name=_("Upgrade system"),
        description=_("Upgrading the system to the latest version."),
        status=JobStatus.CREATED,
    )
    rebuild_system_task(job, upgrade=True)
    return job


async def reboot_system() -> None:
    """Reboot the system"""
    await systemd_proxy().reboot()


def get_system_version() -> str:
    """Get system version"""
    return subprocess.check_output(["uname", "-a"]).decode("utf-8").strip()


def get_python_version() -> str:
    """Get Python version"""
    return subprocess.check_output(["python", "-V"]).decode("utf-8").strip()


class SystemActionResult(BaseModel):
    """System action result"""

    status: int
    message: str
    data: str
