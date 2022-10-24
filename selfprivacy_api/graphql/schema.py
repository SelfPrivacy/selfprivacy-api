"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods

import asyncio
import async_timeout
import redis.asyncio as redis

from typing import AsyncGenerator
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.api_mutations import ApiMutations
from selfprivacy_api.graphql.mutations.job_mutations import JobMutations
from selfprivacy_api.graphql.mutations.mutation_interface import GenericMutationReturn
from selfprivacy_api.graphql.mutations.services_mutations import ServicesMutations
from selfprivacy_api.graphql.mutations.ssh_mutations import SshMutations
from selfprivacy_api.graphql.mutations.storage_mutations import StorageMutations
from selfprivacy_api.graphql.mutations.system_mutations import SystemMutations

from selfprivacy_api.graphql.queries.api_queries import Api
from selfprivacy_api.graphql.queries.jobs import Job
from selfprivacy_api.graphql.queries.services import Services
from selfprivacy_api.graphql.queries.storage import Storage
from selfprivacy_api.graphql.queries.system import System

from selfprivacy_api.graphql.mutations.users_mutations import UserMutations
from selfprivacy_api.graphql.queries.users import Users
from selfprivacy_api.jobs.test import test_job


@strawberry.type
class Query:
    """Root schema for queries"""

    @strawberry.field(permission_classes=[IsAuthenticated])
    def system(self) -> System:
        """System queries"""
        return System()

    @strawberry.field
    def api(self) -> Api:
        """API access status"""
        return Api()

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


@strawberry.type
class Mutation(
    ApiMutations,
    SystemMutations,
    UserMutations,
    SshMutations,
    StorageMutations,
    ServicesMutations,
    JobMutations,
):
    """Root schema for mutations"""

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
        r = redis.from_url('unix:///run/redis-sp-api/redis.sock')
        pubsub = r.pubsub()
        await pubsub.psubscribe("__keyspace@0__:api_test")
        while True:
            try:
                async with async_timeout.timeout(1):
                    message = await pubsub.get_message()
                    if message:
                        if message['data'] == 'set':
                            await r.get('api_test')
                            yield int(await r.get('api_test'))
                    else:
                        await asyncio.sleep(0.01)
            except asyncio.TimeoutError:
                pass



schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
