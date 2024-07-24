"""Services module."""

import base64
import typing
from typing import List
from os import path, mkdir
from pathlib import Path

from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.forgejo import Forgejo
from selfprivacy_api.services.jitsimeet import JitsiMeet
from selfprivacy_api.services.prometheus import Prometheus
from selfprivacy_api.services.roundcube import Roundcube
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.ocserv import Ocserv

from selfprivacy_api.services.service import Service, ServiceDnsRecord
from selfprivacy_api.services.service import ServiceStatus
import selfprivacy_api.utils.network as network_utils

from selfprivacy_api.services.test_service.icon import BITWARDEN_ICON
from selfprivacy_api.utils import USERDATA_FILE, DKIM_DIR, SECRETS_FILE
from selfprivacy_api.utils.block_devices import BlockDevices
from shutil import copyfile, copytree, rmtree

CONFIG_STASH_DIR = "/tmp/selfprivacy_config_dump"


class ServiceManager(Service):
    folders: List[str] = [CONFIG_STASH_DIR]

    @staticmethod
    def get_all_services() -> list[Service]:
        return services

    @staticmethod
    def get_service_by_id(service_id: str) -> typing.Optional[Service]:
        for service in services:
            if service.get_id() == service_id:
                return service
        return None

    @staticmethod
    def get_enabled_services() -> list[Service]:
        return [service for service in services if service.is_enabled()]

    # This one is not currently used by any code.
    @staticmethod
    def get_disabled_services() -> list[Service]:
        return [service for service in services if not service.is_enabled()]

    @staticmethod
    def get_services_by_location(location: str) -> list[Service]:
        return [service for service in services if service.get_drive() == location]

    @staticmethod
    def get_all_required_dns_records() -> list[ServiceDnsRecord]:
        ip4 = network_utils.get_ip4()
        ip6 = network_utils.get_ip6()
        dns_records: list[ServiceDnsRecord] = [
            ServiceDnsRecord(
                type="A",
                name="api",
                content=ip4,
                ttl=3600,
                display_name="SelfPrivacy API",
            ),
        ]

        if ip6 is not None:
            dns_records.append(
                ServiceDnsRecord(
                    type="AAAA",
                    name="api",
                    content=ip6,
                    ttl=3600,
                    display_name="SelfPrivacy API (IPv6)",
                )
            )
        for service in ServiceManager.get_enabled_services():
            dns_records += service.get_dns_records(ip4, ip6)
        return dns_records

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "api"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Selfprivacy API"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "A proto-service for API itself. Currently manages backups of settings."

    @staticmethod
    def get_svg_icon() -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        # return ""
        return base64.b64encode(BITWARDEN_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        # TODO : placeholder, get actual domain here
        return f"https://domain"

    @staticmethod
    def get_subdomain() -> typing.Optional[str]:
        return None

    @classmethod
    def is_movable(cls) -> bool:
        return False

    @staticmethod
    def is_required() -> bool:
        return True

    @staticmethod
    def is_enabled() -> bool:
        return True

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


services: list[Service] = [
    Bitwarden(),
    Forgejo(),
    MailServer(),
    Nextcloud(),
    Pleroma(),
    Ocserv(),
    JitsiMeet(),
    Roundcube(),
    ServiceManager(),
    Prometheus(),
]
