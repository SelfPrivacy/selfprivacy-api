"""Class representing Dovecot and Postfix services"""

import base64
import subprocess
import typing

from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.services.generic_service_mover import FolderMoveNames, move_service
from selfprivacy_api.services.generic_size_counter import get_storage_usage
from selfprivacy_api.services.generic_status_getter import (
    get_service_status,
    get_service_status_from_several_units,
)
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
import selfprivacy_api.utils as utils
from selfprivacy_api.utils.localization import Localization as L10n
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey
import selfprivacy_api.utils.network as network_utils
from selfprivacy_api.services.mailserver.icon import MAILSERVER_ICON


class MailServer(Service):
    """Class representing mail service"""

    @staticmethod
    def get_id() -> str:
        return "mailserver"

    @staticmethod
    def get_display_name(locale: str = "en") -> str:
        return L10n().get("services.mailserver.display_name", locale)

    @staticmethod
    def get_description(locale: str = "en") -> str:
        return L10n().get("services.mailserver.description", locale)

    @staticmethod
    def get_svg_icon() -> str:
        return base64.b64encode(MAILSERVER_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> typing.Optional[str]:
        """Return service url."""
        return None

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return True

    @staticmethod
    def is_enabled() -> bool:
        return True

    @staticmethod
    def get_status() -> ServiceStatus:
        return get_service_status_from_several_units(
            ["dovecot2.service", "postfix.service"]
        )

    @staticmethod
    def enable():
        raise NotImplementedError("enable is not implemented for MailServer")

    @staticmethod
    def disable():
        raise NotImplementedError("disable is not implemented for MailServer")

    @staticmethod
    def stop():
        subprocess.run(["systemctl", "stop", "dovecot2.service"])
        subprocess.run(["systemctl", "stop", "postfix.service"])

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "dovecot2.service"])
        subprocess.run(["systemctl", "start", "postfix.service"])

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "dovecot2.service"])
        subprocess.run(["systemctl", "restart", "postfix.service"])

    @staticmethod
    def get_configuration():
        return {}

    @staticmethod
    def set_configuration(config_items):
        return super().set_configuration(config_items)

    @staticmethod
    def get_logs():
        return ""

    @staticmethod
    def get_storage_usage() -> int:
        return get_storage_usage("/var/vmail")

    @staticmethod
    def get_location() -> str:
        with utils.ReadUserData() as user_data:
            if user_data.get("useBinds", False):
                return user_data.get("mailserver", {}).get("location", "sda1")
            else:
                return "sda1"

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        domain = utils.get_domain()
        dkim_record = utils.get_dkim_key(domain)
        ip4 = network_utils.get_ip4()
        ip6 = network_utils.get_ip6()

        if dkim_record is None:
            return []

        return [
            ServiceDnsRecord(
                type="A",
                name=domain,
                content=ip4,
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="AAAA",
                name=domain,
                content=ip6,
                ttl=3600,
            ),
            ServiceDnsRecord(
                type="MX", name=domain, content=domain, ttl=3600, priority=10
            ),
            ServiceDnsRecord(
                type="TXT", name="_dmarc", content=f"v=DMARC1; p=none", ttl=18000
            ),
            ServiceDnsRecord(
                type="TXT",
                name=domain,
                content=f"v=spf1 a mx ip4:{ip4} -all",
                ttl=18000,
            ),
            ServiceDnsRecord(
                type="TXT", name="selector._domainkey", content=dkim_record, ttl=18000
            ),
        ]

    def move_to_volume(self, volume: BlockDevice, locale: str = "en") -> Job:
        job = Jobs.add(
            type_id="services.mailserver.move",
            name=L10n().get("services.mailserver.move_job.name", locale),
            description=L10n()
            .get("services.mailserver.move_job.description", locale)
            .format(volume=volume.name),
        )

        move_service(
            self,
            volume,
            job,
            [
                FolderMoveNames(
                    name="vmail",
                    bind_location="/var/vmail",
                    group="virtualMail",
                    owner="virtualMail",
                ),
                FolderMoveNames(
                    name="sieve",
                    bind_location="/var/sieve",
                    group="virtualMail",
                    owner="virtualMail",
                ),
            ],
            "mailserver",
        )

        return job
