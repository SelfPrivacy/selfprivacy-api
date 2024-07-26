"""Actions to manage the system."""

import os
import subprocess
import pytz
from typing import Optional, List
from pydantic import BaseModel
from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.jobs.upgrade_system import rebuild_system_task

from selfprivacy_api.utils import WriteUserData, ReadUserData


def get_timezone() -> str:
    """Get the timezone of the server"""
    with ReadUserData() as user_data:
        if "timezone" in user_data:
            return user_data["timezone"]
        return "Etc/UTC"


class InvalidTimezone(Exception):
    """Invalid timezone"""

    pass


def change_timezone(timezone: str) -> None:
    """Change the timezone of the server"""
    if timezone not in pytz.all_timezones:
        raise InvalidTimezone(f"Invalid timezone: {timezone}")
    with WriteUserData() as user_data:
        user_data["timezone"] = timezone


class UserDataAutoUpgradeSettings(BaseModel):
    """Settings for auto-upgrading user data"""

    enable: bool = True
    allowReboot: bool = False


def get_auto_upgrade_settings() -> UserDataAutoUpgradeSettings:
    """Get the auto-upgrade settings"""
    with ReadUserData() as user_data:
        if "autoUpgrade" in user_data:
            return UserDataAutoUpgradeSettings(**user_data["autoUpgrade"])
        return UserDataAutoUpgradeSettings()


def set_auto_upgrade_settings(
    enalbe: Optional[bool] = None, allowReboot: Optional[bool] = None
) -> None:
    """Set the auto-upgrade settings"""
    with WriteUserData() as user_data:
        if "autoUpgrade" not in user_data:
            user_data["autoUpgrade"] = {}
        if enalbe is not None:
            user_data["autoUpgrade"]["enable"] = enalbe
        if allowReboot is not None:
            user_data["autoUpgrade"]["allowReboot"] = allowReboot


class ShellException(Exception):
    """Something went wrong when calling another process"""

    pass


def run_blocking(cmd: List[str], new_session: bool = False) -> str:
    """Run a process, block until done, return output, complain if failed"""
    process_handle = subprocess.Popen(
        cmd,
        shell=False,
        start_new_session=new_session,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout_raw, stderr_raw = process_handle.communicate()
    stdout = stdout_raw.decode("utf-8")
    if stderr_raw is not None:
        stderr = stderr_raw.decode("utf-8")
    else:
        stderr = ""
    output = stdout + "\n" + stderr
    if process_handle.returncode != 0:
        raise ShellException(
            f"Shell command failed, command array: {cmd}, output: {output}"
        )
    return stdout


def rebuild_system() -> Job:
    """Rebuild the system"""
    job = Jobs.add(
        type_id="system.nixos.rebuild",
        name="Rebuild system",
        description="Applying the new system configuration by building the new NixOS generation.",
        status=JobStatus.CREATED,
    )
    rebuild_system_task(job)
    return job


def rollback_system() -> int:
    """Rollback the system"""
    run_blocking(["systemctl", "start", "sp-nixos-rollback.service"], new_session=True)
    return 0


def upgrade_system() -> Job:
    """Upgrade the system"""
    job = Jobs.add(
        type_id="system.nixos.upgrade",
        name="Upgrade system",
        description="Upgrading the system to the latest version.",
        status=JobStatus.CREATED,
    )
    rebuild_system_task(job, upgrade=True)
    return job


def reboot_system() -> None:
    """Reboot the system"""
    run_blocking(["reboot"], new_session=True)


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


def pull_repository_changes() -> SystemActionResult:
    """Pull repository changes"""
    git_pull_command = ["git", "pull"]

    current_working_directory = os.getcwd()
    os.chdir("/etc/nixos")

    git_pull_process_descriptor = subprocess.Popen(
        git_pull_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
    )

    data = git_pull_process_descriptor.communicate()[0].decode("utf-8")

    os.chdir(current_working_directory)

    if git_pull_process_descriptor.returncode == 0:
        return SystemActionResult(
            status=0,
            message="Pulled repository changes",
            data=data,
        )
    return SystemActionResult(
        status=git_pull_process_descriptor.returncode,
        message="Failed to pull repository changes",
        data=data,
    )
