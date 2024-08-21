"""Class representing the configs of our API
Mostly for backupping purposes
"""

import base64
import typing

from typing import List
from os import path, mkdir
from pathlib import Path

# from enum import Enum

from selfprivacy_api.services.service import Service, ServiceStatus

from selfprivacy_api.services.test_service.icon import BITWARDEN_ICON
from selfprivacy_api.utils import USERDATA_FILE, DKIM_DIR, SECRETS_FILE
from selfprivacy_api.utils.block_devices import BlockDevices
from shutil import copyfile, copytree, rmtree


from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.gitea import Gitea
from selfprivacy_api.services.jitsimeet import JitsiMeet
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.ocserv import Ocserv


CONFIG_STASH_DIR = "/tmp/selfprivacy_config_dump"


# it is too intimately tied to Services
# that's why it is so awkward.
# service list is below


class ConfigService(Service):
    """A fake service to store our configs"""

    folders: List[str] = [CONFIG_STASH_DIR]

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "testservice"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Test Service"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "A small service used for test purposes. Does nothing."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        # return ""
        return base64.b64encode(BITWARDEN_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = "test.com"
        return f"https://password.{domain}"

    @staticmethod
    def get_subdomain() -> typing.Optional[str]:
        return "password"

    @classmethod
    def is_movable(cls) -> bool:
        return False

    @staticmethod
    def is_required() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "How did we get here?"

    @classmethod
    def status_file(cls) -> str:
        dir = cls.folders[0]
        # We do not want to store our state in our declared folders
        # Because they are moved and tossed in tests wildly
        parent = Path(dir).parent

        return path.join(parent, "service_status")

    @classmethod
    def set_status(cls, status: ServiceStatus):
        pass

    @classmethod
    def get_status(cls) -> ServiceStatus:
        return ServiceStatus.ACTIVE

    @classmethod
    def can_be_backed_up(cls) -> bool:
        """`True` if the service can be backed up."""
        return True

    @staticmethod
    def merge_settings(restored_settings_folder: str):
        # For now we will just copy settings EXCEPT the locations of services
        # Stash locations as they are set by user right now
        locations = {}
        for service in services:
            locations[service.get_id()] = service.get_drive()

        # Copy files
        userdata_name = path.basename(USERDATA_FILE)
        secretfile_name = path.basename(SECRETS_FILE)
        dkim_dirname = path.basename(DKIM_DIR)

        copyfile(path.join(restored_settings_folder, userdata_name), USERDATA_FILE)
        copyfile(path.join(restored_settings_folder, secretfile_name), SECRETS_FILE)
        copytree(path.join(restored_settings_folder, dkim_dirname), DKIM_DIR)

        # Pop locations
        for service in services:
            device = BlockDevices().get_block_device(locations[service.get_id()])
            if device is not None:
                service.set_location(device.name)

    @classmethod
    def stop(cls):
        # simulate a failing service unable to stop
        if not cls.get_status() == ServiceStatus.FAILED:
            cls.set_status(ServiceStatus.DEACTIVATING)
            cls.change_status_with_async_delay(
                ServiceStatus.INACTIVE, cls.startstop_delay
            )

    @classmethod
    def start(cls):
        pass

    @classmethod
    def restart(cls):
        pass

    @staticmethod
    def get_logs():
        return ""

    @classmethod
    def get_drive(cls) -> str:
        return BlockDevices().get_root_block_device().name

    @classmethod
    def get_folders(cls) -> List[str]:
        return cls.folders

    @classmethod
    def pre_backup(cls):
        tempdir = cls.folders[0]
        rmtree(tempdir, ignore_errors=True)
        mkdir(tempdir)

        copyfile(USERDATA_FILE, tempdir)
        copyfile(SECRETS_FILE, tempdir)
        copytree(DKIM_DIR, tempdir)

    @classmethod
    def post_restore(cls):
        tempdir = cls.folders[0]
        cls.merge_settings(tempdir)
        rmtree(tempdir, ignore_errors=True)


# It is here because our thing needs to include itself
services: list[Service] = [
    Bitwarden(),
    Gitea(),
    MailServer(),
    Nextcloud(),
    Pleroma(),
    Ocserv(),
    JitsiMeet(),
    ConfigService(),
]
