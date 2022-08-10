"""GraphQL API for SelfPrivacy."""
# pylint: disable=too-few-public-methods
import typing
from strawberry.permission import BasePermission
from strawberry.types import Info

from selfprivacy_api.utils.auth import is_token_valid


class IsAuthenticated(BasePermission):
    """Is authenticated permission"""

    message = "You must be authenticated to access this resource."

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        return info.context.is_authenticated
