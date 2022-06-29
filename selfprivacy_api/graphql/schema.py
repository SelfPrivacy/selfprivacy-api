"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.api_mutations import ApiMutations

from selfprivacy_api.graphql.queries.api_queries import Api
from selfprivacy_api.graphql.queries.system import System


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

@strawberry.type
class Mutation(ApiMutations):
    """Root schema for mutations"""
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)
