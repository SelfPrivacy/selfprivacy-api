"""Class representing Dovecot and Postfix services"""

import base64
import subprocess
from typing import Optional, List

from selfprivacy_api.utils.systemd import (
    get_service_status_from_several_units,
)
from selfprivacy_api.services.service import Service, ServiceDnsRecord, ServiceStatus
from selfprivacy_api import utils
from selfprivacy_api.services.mailserver.icon import MAILSERVER_ICON


class MailServer(Service):
    """Class representing mail service"""

    @staticmethod
    def get_id() -> str:
        return "simple-nixos-mailserver"

    @staticmethod
    def get_display_name() -> str:
        return "Mail Server"

    @staticmethod
    def get_description() -> str:
        return "E-Mail for company and family."

    @staticmethod
    def get_svg_icon() -> str:
        return base64.b64encode(MAILSERVER_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_user() -> str:
        return "virtualMail"

    @classmethod
    def get_url(cls) -> Optional[str]:
        """Return service url."""
        return None

    @classmethod
    def get_subdomain(cls) -> Optional[str]:
        return None

    @staticmethod
    def is_movable() -> bool:
        return True

    @staticmethod
    def is_required() -> bool:
        return True

    @staticmethod
    def get_backup_description() -> str:
        return "Mail boxes and filters."

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
        subprocess.run(["systemctl", "stop", "dovecot2.service"], check=False)
        subprocess.run(["systemctl", "stop", "postfix.service"], check=False)

    @staticmethod
    def start():
        subprocess.run(["systemctl", "start", "dovecot2.service"], check=False)
        subprocess.run(["systemctl", "start", "postfix.service"], check=False)

    @staticmethod
    def restart():
        subprocess.run(["systemctl", "restart", "dovecot2.service"], check=False)
        subprocess.run(["systemctl", "restart", "postfix.service"], check=False)

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
    def get_folders() -> List[str]:
        return ["/var/vmail", "/var/sieve"]

    @classmethod
    def get_dns_records(cls, ip4: str, ip6: Optional[str]) -> List[ServiceDnsRecord]:
        domain = utils.get_domain()
        dkim_record = utils.get_dkim_key(domain)

        if dkim_record is None:
            return []

        dns_records = [
            ServiceDnsRecord(
                type="A",
                name=domain,
                content=ip4,
                ttl=3600,
                display_name="Root Domain",
            ),
            ServiceDnsRecord(
                type="MX",
                name=domain,
                content=domain,
                ttl=3600,
                priority=10,
                display_name="Mail server record",
            ),
            ServiceDnsRecord(
                type="TXT",
                name="_dmarc",
                content="v=DMARC1; p=none",
                ttl=18000,
                display_name="DMARC record",
            ),
            ServiceDnsRecord(
                type="TXT",
                name=domain,
                content=f"v=spf1 a mx ip4:{ip4} -all",
                ttl=18000,
                display_name="SPF record",
            ),
            ServiceDnsRecord(
                type="TXT",
                name="selector._domainkey",
                content=dkim_record,
                ttl=18000,
                display_name="DKIM key",
            ),
        ]

        if ip6 is not None:
            dns_records.append(
                ServiceDnsRecord(
                    type="AAAA",
                    name=domain,
                    content=ip6,
                    ttl=3600,
                    display_name="Root Domain (IPv6)",
                ),
            )
        return dns_records
