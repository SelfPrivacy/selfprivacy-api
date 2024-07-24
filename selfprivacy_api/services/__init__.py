"""Services module."""

import typing
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
import selfprivacy_api.utils.network as network_utils

services: list[Service] = [
    Bitwarden(),
    Forgejo(),
    MailServer(),
    Nextcloud(),
    Pleroma(),
    Ocserv(),
    JitsiMeet(),
    Roundcube(),
    Prometheus(),
]


class ServiceManager(Service):
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
        for service in get_enabled_services():
            dns_records += service.get_dns_records(ip4, ip6)
        return dns_records
