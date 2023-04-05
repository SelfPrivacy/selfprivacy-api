"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods
import typing
from strawberry.permission import BasePermission
from strawberry.types import Info

from selfprivacy_api.actions.api_tokens import is_token_valid


class IsAuthenticated(BasePermission):
    """Is authenticated permission"""

    message = "You must be authenticated to access this resource."

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        token = info.context["request"].headers.get("Authorization")
        if token is None:
            token = info.context["request"].query_params.get("token")
        if token is None:
            return False
        return is_token_valid(token.replace("Bearer ", ""))
