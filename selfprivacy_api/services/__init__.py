"""Services module."""

import typing
from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.gitea import Gitea
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.ocserv import Ocserv
from selfprivacy_api.services.service import Service


services: list[Service] = [
    Bitwarden(),
    Gitea(),
    MailServer(),
    Nextcloud(),
    Pleroma(),
    Ocserv(),
]


def get_all_services() -> typing.List[Service]:
    return services


def get_service_by_id(service_id: str) -> typing.Optional[Service]:
    for service in services:
        if service.get_id() == service_id:
            return service
    return None


def get_enabled_services() -> typing.List[Service]:
    return [service for service in services if service.is_enabled()]


def get_disabled_services() -> typing.List[Service]:
    return [service for service in services if not service.is_enabled()]


def get_services_by_location(location: str) -> typing.List[Service]:
    return [service for service in services if service.get_location() == location]
