"""Services status"""

# pylint: disable=too-few-public-methods
import asyncio
import typing
from opentelemetry import trace

import strawberry

from selfprivacy_api.graphql.common_types.service import (
    Service,
    service_to_graphql_service,
)
from selfprivacy_api.services import ServiceManager

tracer = trace.get_tracer(__name__)


@strawberry.type
class Services:
    @strawberry.field
    async def all_services(self) -> typing.List[Service]:
        with tracer.start_as_current_span("resolve_all_services") as span:
            services = await asyncio.get_event_loop().run_in_executor(
                None, ServiceManager.get_all_services
            )
            services = [
                await service_to_graphql_service(service) for service in services
            ]

            span.set_attribute("service_count", len(services))
            span.add_event("fetched all services from service manager")

            return sorted(services, key=lambda service: service.display_name)
