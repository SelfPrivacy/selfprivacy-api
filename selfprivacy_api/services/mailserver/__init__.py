"""Class representing Dovecot and Postfix services"""

import base64
import subprocess
import typing

from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.services.generic_service_mover import FolderMoveNames, move_service
from selfprivacy_api.services.generic_size_counter import get_storage_usage
from selfprivacy_api.services.generic_status_getter import get_service_status
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api.utils import ReadUserData, WriteUserData, get_dkim_key, get_domain
from selfprivacy_api.utils import huey
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import Huey
from selfprivacy_api.utils.network import get_ip4

huey = Huey()


class MailServer(Service):
    """Class representing mail service"""

    @staticmethod
    def get_id() -> str:
        return "mailserver"

    @staticmethod
    def get_display_name() -> str:
        return "Mail Server"

    @staticmethod
    def get_description() -> str:
        return "E-Mail for company and family."

    @staticmethod
    def get_svg_icon() -> str:
        with open("selfprivacy_api/services/mailserver/mailserver.svg", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

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
        imap_status = get_service_status("dovecot2.service")
        smtp_status = get_service_status("postfix.service")

        if (
            imap_status == ServiceStatus.RUNNING
            and smtp_status == ServiceStatus.RUNNING
        ):
            return ServiceStatus.RUNNING
        elif imap_status == ServiceStatus.ERROR or smtp_status == ServiceStatus.ERROR:
            return ServiceStatus.ERROR
        elif (
            imap_status == ServiceStatus.STOPPED or smtp_status == ServiceStatus.STOPPED
        ):
            return ServiceStatus.STOPPED
        elif imap_status == ServiceStatus.OFF or smtp_status == ServiceStatus.OFF:
            return ServiceStatus.OFF
        else:
            return ServiceStatus.DEGRADED

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
        with ReadUserData() as user_data:
            if user_data.get("useBinds", False):
                return user_data.get("mailserver", {}).get("location", "sda1")
            else:
                return "sda1"

    @staticmethod
    def get_dns_records() -> typing.List[ServiceDnsRecord]:
        domain = get_domain()
        dkim_record = get_dkim_key(domain)
        ip4 = get_ip4()

        if dkim_record is None:
            return []

        return [
            ServiceDnsRecord(
                type="MX", name=domain, content=domain, ttl=3600, priority=10
            ),
            ServiceDnsRecord(
                type="TXT", name="_dmarc", content=f"v=DMARC1; p=none", ttl=3600
            ),
            ServiceDnsRecord(
                type="TXT", name=domain, content=f"v=spf1 a mx ip4:{ip4} -all", ttl=3600
            ),
            ServiceDnsRecord(
                type="TXT", name="selector._domainkey", content=dkim_record, ttl=3600
            ),
        ]

    def move_to_volume(self, volume: BlockDevice):
        job = Jobs.get_instance().add(
            name="services.mailserver.move",
            description=f"Moving mailserver data to {volume.name}",
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
