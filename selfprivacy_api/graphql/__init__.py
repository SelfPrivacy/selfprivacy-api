"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.queries.system import System
from selfprivacy_api.graphql.queries.api import Api

@strawberry.type
class Query:
    """Root schema for queries"""
    system: System
    api: Api

schema = strawberry.Schema(query=Query)
