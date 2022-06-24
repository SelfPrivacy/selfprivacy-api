"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.queries.api import Api
from selfprivacy_api.graphql.queries.system import System


@strawberry.type
class Query:
    """Root schema for queries"""

    @strawberry.field
    def system(self) -> System:
        """System queries"""
        return System()

    @strawberry.field
    def api(self) -> Api:
        """API access status"""
        return Api()


schema = strawberry.Schema(query=Query)
