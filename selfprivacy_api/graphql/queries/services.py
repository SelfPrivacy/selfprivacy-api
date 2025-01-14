"""Services status"""

# pylint: disable=too-few-public-methods
import typing

import strawberry

from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)
from selfprivacy_api.services import ServiceManager


@strawberry.type
class Services:
    @strawberry.field
    def all_services(self) -> typing.List[Service]:
        services = [
            service_to_graphql_service(service)
            for service in ServiceManager.get_all_services()
        ]
        return sorted(services, key=lambda service: service.display_name)
