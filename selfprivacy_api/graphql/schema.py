"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods

import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.api_mutations import ApiMutations
from selfprivacy_api.graphql.mutations.ssh_mutations import SshMutations
from selfprivacy_api.graphql.mutations.storage_mutation import StorageMutations
from selfprivacy_api.graphql.mutations.system_mutations import SystemMutations

from selfprivacy_api.graphql.queries.api_queries import Api
from selfprivacy_api.graphql.queries.storage import Storage
from selfprivacy_api.graphql.queries.system import System

from selfprivacy_api.graphql.mutations.users_mutations import UserMutations
from selfprivacy_api.graphql.queries.users import Users


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


@strawberry.type
class Mutation(
    ApiMutations,
    SystemMutations,
    UserMutations,
    SshMutations,
    StorageMutations,
):
    """Root schema for mutations"""

    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
