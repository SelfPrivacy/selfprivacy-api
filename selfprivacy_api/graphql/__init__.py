"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from strawberry.permission import BasePermission
from strawberry.types import Info
from flask import request

from selfprivacy_api.graphql.queries.api import Api
from selfprivacy_api.graphql.queries.system import System
from selfprivacy_api.utils.auth import is_token_valid

class IsAuthenticated(BasePermission):
    """Is authenticated permission"""
    message = "You must be authenticated to access this resource."

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        auth = request.headers.get("Authorization")
        if auth is None:
            return False
        # Strip Bearer from auth header
        auth = auth.replace("Bearer ", "")
        if not is_token_valid(auth):
            return False
        return True


@strawberry.type
class Query:
    """Root schema for queries"""
    system: System
    @strawberry.field(permission_classes=[IsAuthenticated])
    def api(self) -> Api:
        """API access status"""
        return Api()

schema = strawberry.Schema(query=Query)
