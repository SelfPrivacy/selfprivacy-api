"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods

import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.api_mutations import ApiMutations
from selfprivacy_api.graphql.mutations.mutation_interface import GenericMutationReturn
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
):
    """Root schema for mutations"""

    @strawberry.mutation
    def test_mutation(self) -> GenericMutationReturn:
        """Test mutation"""
        test_job()
        return GenericMutationReturn(
            success=True,
            message="Test mutation",
            code=200,
        )

    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
