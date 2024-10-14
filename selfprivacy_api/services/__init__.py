"""Services module."""

import base64
import typing
from typing import List
from os import path, remove
from os import makedirs
from os import listdir
from os.path import join

from shutil import copyfile, copytree, rmtree
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

from selfprivacy_api.services.api_icon import API_ICON
from selfprivacy_api.utils import USERDATA_FILE, DKIM_DIR, SECRETS_FILE, get_domain
from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.utils import read_account_uri

CONFIG_STASH_DIR = "/etc/selfprivacy/dump"


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

        dns_records: list[ServiceDnsRecord] = []

        try:
            dns_records.append(
                ServiceDnsRecord(
                    type="CAA",
                    name=get_domain(),
                    content=f'128 issue "letsencrypt.org;accounturi={read_account_uri()}"',
                    ttl=3600,
                    display_name="CAA record",
                )
            )
        except Exception as e:
            print(f"Error creating CAA: {e}")

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
        return base64.b64encode(API_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = get_domain()
        subdomain = ServiceManager.get_subdomain()
        return f"https://{subdomain}.{domain}" if subdomain else None

    @staticmethod
    def get_subdomain() -> typing.Optional[str]:
        return "api"

    @staticmethod
    def is_always_active() -> bool:
        return True

    @staticmethod
    def is_movable() -> bool:
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
    def get_status(cls) -> ServiceStatus:
        return ServiceStatus.ACTIVE

    @classmethod
    def can_be_backed_up(cls) -> bool:
        """`True` if the service can be backed up."""
        return True

    @classmethod
    def merge_settings(cls):
        # For now we will just copy settings EXCEPT the locations of services
        # Stash locations as they are set by user right now
        locations = {}
        for service in services:
            locations[service.get_id()] = service.get_drive()

        # Copy files
        for p in [USERDATA_FILE, SECRETS_FILE, DKIM_DIR]:
            cls.retrieve_stashed_path(p)

        # Pop locations
        for service in services:
            device = BlockDevices().get_block_device(locations[service.get_id()])
            if device is not None:
                service.set_location(device)

    @classmethod
    def stop(cls):
        """
        We are always active
        """
        raise ValueError("tried to stop an always active service")

    @classmethod
    def start(cls):
        """
        We are always active
        """
        pass

    @classmethod
    def restart(cls):
        """
        We are always active
        """
        pass

    @staticmethod
    def get_logs():
        # TODO: maybe return the logs for api itself
        return ""

    @classmethod
    def get_drive(cls) -> str:
        return BlockDevices().get_root_block_device().name

    @classmethod
    def get_folders(cls) -> List[str]:
        return cls.folders

    @classmethod
    def stash_for(cls, p: str) -> str:
        basename = path.basename(p)
        stashed_file_location = join(cls.dump_dir(), basename)
        return stashed_file_location

    @classmethod
    def stash_a_path(cls, p: str):
        if path.isdir(p):
            rmtree(cls.stash_for(p), ignore_errors=True)
            copytree(p, cls.stash_for(p))
        else:
            copyfile(p, cls.stash_for(p))

    @classmethod
    def retrieve_stashed_path(cls, p: str):
        """
        Takes an original path, hopefully it is stashed somewhere
        """
        if path.isdir(p):
            rmtree(p, ignore_errors=True)
            copytree(cls.stash_for(p), p)
        else:
            copyfile(cls.stash_for(p), p)

    @classmethod
    def pre_backup(cls):
        tempdir = cls.dump_dir()
        if not path.exists(tempdir):
            makedirs(tempdir)

        paths = listdir(tempdir)
        for file in paths:
            remove(file)

        for p in [USERDATA_FILE, SECRETS_FILE, DKIM_DIR]:
            cls.stash_a_path(p)

    @classmethod
    def dump_dir(cls) -> str:
        """
        A directory we dump our settings into
        """
        return cls.folders[0]

    @classmethod
    def post_restore(cls):
        cls.merge_settings()
        rmtree(cls.dump_dir(), ignore_errors=True)


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
