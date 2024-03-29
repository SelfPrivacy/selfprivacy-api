"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods

import asyncio
from typing import AsyncGenerator
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
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

from selfprivacy_api.graphql.queries.api_queries import Api
from selfprivacy_api.graphql.queries.backup import Backup
from selfprivacy_api.graphql.queries.jobs import Job
from selfprivacy_api.graphql.queries.services import Services
from selfprivacy_api.graphql.queries.storage import Storage
from selfprivacy_api.graphql.queries.system import System

from selfprivacy_api.graphql.mutations.users_mutations import UsersMutations
from selfprivacy_api.graphql.queries.users import Users
from selfprivacy_api.jobs.test import test_job


@strawberry.type
class Query:
    """Root schema for queries"""

    @strawberry.field
    def api(self) -> Api:
        """API access status"""
        return Api()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def system(self) -> System:
        """System queries"""
        return System()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def users(self) -> Users:
        """Users queries"""
        return Users()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def storage(self) -> Storage:
        """Storage queries"""
        return Storage()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def jobs(self) -> Job:
        """Jobs queries"""
        return Job()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def services(self) -> Services:
        """Services queries"""
        return Services()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def backup(self) -> Backup:
        """Backup queries"""
        return Backup()


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
    def api(self) -> ApiMutations:
        """API mutations"""
        return ApiMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def system(self) -> SystemMutations:
        """System mutations"""
        return SystemMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def users(self) -> UsersMutations:
        """Users mutations"""
        return UsersMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def storage(self) -> StorageMutations:
        """Storage mutations"""
        return StorageMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def services(self) -> ServicesMutations:
        """Services mutations"""
        return ServicesMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def jobs(self) -> JobMutations:
        """Jobs mutations"""
        return JobMutations()

    @strawberry.field(permission_classes=[IsAuthenticated])
    def backup(self) -> BackupMutations:
        """Backup mutations"""
        return BackupMutations()

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def test_mutation(self) -> GenericMutationReturn:
        """Test mutation"""
        test_job()
        return GenericMutationReturn(
            success=True,
            message="Test mutation",
            code=200,
        )

    pass


@strawberry.type
class Subscription:
    """Root schema for subscriptions"""

    @strawberry.subscription(permission_classes=[IsAuthenticated])
    async def count(self, target: int = 100) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)
