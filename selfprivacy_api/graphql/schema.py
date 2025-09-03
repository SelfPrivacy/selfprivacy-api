"""GraphQL API for SelfPrivacy."""

# pylint: disable=too-few-public-methods

import asyncio
from typing import AsyncGenerator, List
import strawberry
from strawberry.types import Info
from strawberry.extensions.tracing import OpenTelemetryExtension

from selfprivacy_api.utils.localization import Localization, DEFAULT_LOCALE

from selfprivacy_api.graphql import IsAuthenticated, LocaleExtension
from selfprivacy_api.graphql.mutations.deprecated_mutations import (
    DeprecatedApiMutations,
    DeprecatedJobMutations,
    DeprecatedServicesMutations,
    DeprecatedStorageMutations,
    DeprecatedSystemMutations,
    DeprecatedUsersMutations,
)
from selfprivacy_api.graphql.mutations.api_mutations import ApiMutations
from selfprivacy_api.graphql.mutations.job_mutations import JobMutations
from selfprivacy_api.graphql.mutations.mutation_interface import GenericMutationReturn
from selfprivacy_api.graphql.mutations.services_mutations import ServicesMutations
from selfprivacy_api.graphql.mutations.storage_mutations import StorageMutations
from selfprivacy_api.graphql.mutations.system_mutations import SystemMutations
from selfprivacy_api.graphql.mutations.backup_mutations import BackupMutations
from selfprivacy_api.graphql.mutations.email_passwords_metadata_mutations import (
    EmailPasswordsMetadataMutations,
)
from selfprivacy_api.graphql.mutations.kanidm_mutations import KanidmMutations

from selfprivacy_api.graphql.queries.api_queries import Api
from selfprivacy_api.graphql.queries.backup import Backup
from selfprivacy_api.graphql.queries.groups import Groups
from selfprivacy_api.graphql.queries.jobs import Job
from selfprivacy_api.graphql.queries.logs import LogEntry, Logs
from selfprivacy_api.graphql.queries.services import Services
from selfprivacy_api.graphql.queries.storage import Storage
from selfprivacy_api.graphql.queries.system import System
from selfprivacy_api.graphql.queries.monitoring import Monitoring
from selfprivacy_api.graphql.queries.kanidm import Kanidm

from selfprivacy_api.graphql.subscriptions.jobs import ApiJob
from selfprivacy_api.graphql.subscriptions.jobs import (
    job_updates as job_update_generator,
)
from selfprivacy_api.graphql.subscriptions.logs import log_stream

from selfprivacy_api.graphql.common_types.service import (
    StringConfigItem,
    BoolConfigItem,
    EnumConfigItem,
)

from selfprivacy_api.graphql.mutations.users_mutations import UsersMutations
from selfprivacy_api.graphql.queries.users import Users
from selfprivacy_api.jobs.test import test_job


@strawberry.type
class Query:
    """Root schema for queries"""

    @strawberry.field
    async def api(self) -> Api:
        """API access status"""
        return Api()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system(self) -> System:
        """System queries"""
        return System()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def logs(self) -> Logs:
        """Log queries"""
        return Logs()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def users(self) -> Users:
        """Users queries"""
        return Users()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def groups(self) -> Groups:
        """Users queries"""
        return Groups()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def storage(self) -> Storage:
        """Storage queries"""
        return Storage()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def jobs(self) -> Job:
        """Jobs queries"""
        return Job()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def services(self) -> Services:
        """Services queries"""
        return Services()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def backup(self) -> Backup:
        """Backup queries"""
        return Backup()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def monitoring(self) -> Monitoring:
        """Monitoring queries"""
        return Monitoring()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def kanidm(self) -> Kanidm:
        """Kanidm queries"""
        return Kanidm()


@strawberry.type
class Mutation(
    DeprecatedApiMutations,
    DeprecatedSystemMutations,
    DeprecatedUsersMutations,
    DeprecatedStorageMutations,
    DeprecatedServicesMutations,
    DeprecatedJobMutations,
):
    """Root schema for mutations"""

    @strawberry.field
    async def api(self) -> ApiMutations:
        """API mutations"""
        return ApiMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def system(self) -> SystemMutations:
        """System mutations"""
        return SystemMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def users(self) -> UsersMutations:
        """Users mutations"""
        return UsersMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def storage(self) -> StorageMutations:
        """Storage mutations"""
        return StorageMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def email_password_metadata_mutations(
        self,
    ) -> EmailPasswordsMetadataMutations:
        """Storage mutations"""
        return EmailPasswordsMetadataMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def kanidm_mutations(self) -> KanidmMutations:
        """Kanidm mutations"""
        return KanidmMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def services(self) -> ServicesMutations:
        """Services mutations"""
        return ServicesMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def jobs(self) -> JobMutations:
        """Jobs mutations"""
        return JobMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def backup(self) -> BackupMutations:
        """Backup mutations"""
        return BackupMutations()

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def test_mutation(self) -> GenericMutationReturn:
        """Test mutation"""
        test_job()
        return GenericMutationReturn(
            success=True,
            message="Test mutation",
            code=200,
        )


# A cruft for Websockets
def authenticated(info: Info) -> bool:
    return IsAuthenticated().has_permission(source=None, info=info)


def reject_if_unauthenticated(info: Info):
    if not authenticated(info):
        raise Exception(IsAuthenticated().message)


@strawberry.type
class Subscription:
    """Root schema for subscriptions.
    Every field here should be an AsyncIterator or AsyncGenerator
    It is not a part of the spec but graphql-core (dep of strawberryql)
    demands it while the spec is vague in this area."""

    @strawberry.subscription
    async def job_updates(self, info: Info) -> AsyncGenerator[List[ApiJob], None]:
        reject_if_unauthenticated(info)

        connection_params = info.context.get("connection_params")
        locales_raw = connection_params.get("Accept-Language")

        if locales_raw:
            locale = Localization().get_locale(locales_raw)
        else:
            locale = DEFAULT_LOCALE

        return job_update_generator(locale=locale)

    @strawberry.subscription
    # Used for testing, consider deletion to shrink attack surface
    async def count(self, info: Info) -> AsyncGenerator[int, None]:
        reject_if_unauthenticated(info)
        for i in range(10):
            yield i
            await asyncio.sleep(0.5)

    @strawberry.subscription
    async def log_entries(self, info: Info) -> AsyncGenerator[LogEntry, None]:
        reject_if_unauthenticated(info)
        return log_stream()


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    types=[
        StringConfigItem,
        BoolConfigItem,
        EnumConfigItem,
    ],
    extensions=[
        OpenTelemetryExtension(),
    ],
)
