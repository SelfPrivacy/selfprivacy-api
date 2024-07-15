"""Services status"""

# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)
from selfprivacy_api.services import get_all_services


@strawberry.type
class Services:
    @strawberry.field
    def all_services(self) -> typing.List[Service]:
        services = get_all_services()
        return [service_to_graphql_service(service) for service in services]
