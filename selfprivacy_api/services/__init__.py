"""Services module."""

import logging
import base64
import typing
import subprocess
import json
from typing import List
from os import listdir, path
from os import makedirs
from os.path import join
from functools import lru_cache


from shutil import copyfile, copytree, rmtree
from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.services.prometheus import Prometheus
from selfprivacy_api.services.mailserver import MailServer

from selfprivacy_api.services.service import Service, ServiceDnsRecord
from selfprivacy_api.services.service import ServiceStatus
from selfprivacy_api.utils.cached_call import get_ttl_hash
import selfprivacy_api.utils.network as network_utils

from selfprivacy_api.services.api_icon import API_ICON
from selfprivacy_api.utils import (
    USERDATA_FILE,
    DKIM_DIR,
    SECRETS_FILE,
    get_domain,
    read_account_uri,
)
from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.services.templated_service import (
    SP_MODULES_DEFENITIONS_PATH,
    SP_SUGGESTED_MODULES_PATH,
    TemplatedService,
)

CONFIG_STASH_DIR = "/etc/selfprivacy/dump"
KANIDM_A_RECORD = "auth"

logger = logging.getLogger(__name__)


class ServiceManager(Service):
    folders: List[str] = [CONFIG_STASH_DIR]

    @staticmethod
    def get_all_services() -> list[Service]:
        return get_services()

    @staticmethod
    def get_service_by_id(service_id: str) -> typing.Optional[Service]:
        for service in get_services():
            if service.get_id() == service_id:
                return service
        return None

    @staticmethod
    def get_enabled_services() -> list[Service]:
        return [service for service in get_services() if service.is_enabled()]

    @staticmethod
    def get_enabled_services_with_urls() -> list[Service]:
        return [
            service
            for service in get_services(exclude_remote=True)
            if service.is_enabled() and service.get_url()
        ]

    # This one is not currently used by any code.
    @staticmethod
    def get_disabled_services() -> list[Service]:
        return [service for service in get_services() if not service.is_enabled()]

    @staticmethod
    def get_services_by_location(location: str) -> list[Service]:
        return [
            service
            for service in get_services(
                exclude_remote=True,
            )
            if service.get_drive() == location
        ]

    @staticmethod
    def get_all_required_dns_records() -> list[ServiceDnsRecord]:
        ip4 = network_utils.get_ip4()
        ip6 = network_utils.get_ip6()

        dns_records: list[ServiceDnsRecord] = [
            ServiceDnsRecord(
                type="A",
                name=KANIDM_A_RECORD,
                content=ip4,
                ttl=3600,
                display_name="Record for Kanidm",
            ),
        ]

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
            logging.error(f"Error creating CAA: {e}")

        for service in ServiceManager.get_enabled_services():
            dns_records += service.get_dns_records(ip4, ip6)
        return dns_records

    @staticmethod
    def get_id() -> str:
        """Return service id."""
        return "selfprivacy-api"

    @staticmethod
    def get_display_name() -> str:
        """Return service display name."""
        return "Selfprivacy API"

    @staticmethod
    def get_description() -> str:
        """Return service description."""
        return "Enables communication between the SelfPrivacy app and the server."

    @staticmethod
    def get_svg_icon(raw=False) -> str:
        """Read SVG icon from file and return it as base64 encoded string."""
        if raw:
            return API_ICON
        return base64.b64encode(API_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        domain = get_domain()
        return f"https://api.{domain}"

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
    def is_installed() -> bool:
        return True

    @staticmethod
    def is_system_service() -> bool:
        return True

    @staticmethod
    def get_backup_description() -> str:
        return "General server settings."

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
        for service in get_services(
            exclude_remote=True,
        ):
            if service.is_movable():
                locations[service.get_id()] = service.get_drive()

        # Copy files
        for p in [USERDATA_FILE, SECRETS_FILE, DKIM_DIR]:
            cls.retrieve_stashed_path(p)

        # Pop location
        for service in get_services(
            exclude_remote=True,
        ):
            if service.is_movable():
                device = BlockDevices().get_block_device_by_canonical_name(
                    locations[service.get_id()]
                )
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

    @classmethod
    def get_drive(cls) -> str:
        return BlockDevices().get_root_block_device().canonical_name

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
    def pre_backup(cls, job: Job):
        Jobs.update(
            job,
            status_text="Stashing settings",
            status=JobStatus.RUNNING,
        )
        tempdir = cls.dump_dir()
        rmtree(join(tempdir), ignore_errors=True)
        makedirs(tempdir)

        for p in [USERDATA_FILE, SECRETS_FILE, DKIM_DIR]:
            cls.stash_a_path(p)

    @classmethod
    def post_backup(cls, job: Job):
        rmtree(cls.dump_dir(), ignore_errors=True)

    @classmethod
    def dump_dir(cls) -> str:
        """
        A directory we dump our settings into
        """
        return cls.folders[0]

    @classmethod
    def post_restore(cls, job: Job):
        cls.merge_settings()
        rmtree(cls.dump_dir(), ignore_errors=True)


# @redis_cached_call(ttl=30)
@lru_cache()
def get_templated_service(service_id: str, ttl_hash=None) -> TemplatedService:
    del ttl_hash
    return TemplatedService(service_id)


# @redis_cached_call(ttl=3600)
@lru_cache()
def get_remote_service(id: str, url: str, ttl_hash=None) -> TemplatedService:
    del ttl_hash
    response = subprocess.run(
        ["sp-fetch-remote-module", url],
        capture_output=True,
        text=True,
        check=True,
    )
    return TemplatedService(id, response.stdout)


DUMMY_SERVICES = []
TEST_FLAGS: list[str] = []


def get_services(exclude_remote=False) -> List[Service]:
    if "ONLY_DUMMY_SERVICE" in TEST_FLAGS:
        return DUMMY_SERVICES
    if "DUMMY_SERVICE_AND_API" in TEST_FLAGS:
        return DUMMY_SERVICES + [ServiceManager()]

    hardcoded_services: list[Service] = [
        MailServer(),
        ServiceManager(),
        Prometheus(),
    ]
    if DUMMY_SERVICES:
        hardcoded_services += DUMMY_SERVICES
    service_ids = [service.get_id() for service in hardcoded_services]

    templated_services: List[Service] = []
    if path.exists(SP_MODULES_DEFENITIONS_PATH):
        for module in listdir(SP_MODULES_DEFENITIONS_PATH):
            if module in service_ids:
                continue
            try:
                templated_services.append(
                    get_templated_service(module, ttl_hash=get_ttl_hash(30))
                )
                service_ids.append(module)
            except Exception as e:
                logger.error(f"Failed to load service {module}: {e}")

    if not exclude_remote and path.exists(SP_SUGGESTED_MODULES_PATH):
        # It is a file with a JSON array
        with open(SP_SUGGESTED_MODULES_PATH) as f:
            suggested_modules = json.load(f)
        for module in suggested_modules:
            if module in service_ids:
                continue
            try:
                templated_services.append(
                    get_remote_service(
                        module,
                        f"git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/{module}",
                        ttl_hash=get_ttl_hash(3600),
                    )
                )
                service_ids.append(module)
            except Exception as e:
                logger.error(f"Failed to load service {module}: {e}")

    logger.warning(f"Loaded services: {service_ids}")

    return hardcoded_services + templated_services
