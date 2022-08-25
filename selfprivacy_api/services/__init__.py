"""Services module."""

import typing
from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.gitea import Gitea
from selfprivacy_api.services.jitsi import Jitsi
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.ocserv import Ocserv
from selfprivacy_api.services.service import Service, ServiceDnsRecord
import selfprivacy_api.utils.network as network_utils

services: list[Service] = [
    Bitwarden(),
    Gitea(),
    MailServer(),
    Nextcloud(),
    Pleroma(),
    Ocserv(),
    Jitsi(),
]


def get_all_services() -> list[Service]:
    return services


def get_service_by_id(service_id: str) -> typing.Optional[Service]:
    for service in services:
        if service.get_id() == service_id:
            return service
    return None


def get_enabled_services() -> list[Service]:
    return [service for service in services if service.is_enabled()]


def get_disabled_services() -> list[Service]:
    return [service for service in services if not service.is_enabled()]


def get_services_by_location(location: str) -> list[Service]:
    return [service for service in services if service.get_location() == location]


def get_all_required_dns_records() -> list[ServiceDnsRecord]:
    ip4 = network_utils.get_ip4()
    ip6 = network_utils.get_ip6()
    dns_records: list[ServiceDnsRecord] = [
        ServiceDnsRecord(
            type="A",
            name="api",
            content=ip4,
            ttl=3600,
        ),
        ServiceDnsRecord(
            type="AAAA",
            name="api",
            content=ip6,
            ttl=3600,
        ),
    ]
    for service in get_enabled_services():
        dns_records += service.get_dns_records()
    return dns_records
