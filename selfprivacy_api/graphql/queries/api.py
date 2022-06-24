"""API access status"""
# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.queries.api_fields import ApiDevice, ApiRecoveryKeyStatus
from selfprivacy_api.resolvers.api import get_api_version, get_devices, get_recovery_key_status


@strawberry.type
class Api:
    """API access status"""
    version: str = strawberry.field(resolver=get_api_version)
    devices: typing.List[ApiDevice] = strawberry.field(resolver=get_devices)
    recovery_key: ApiRecoveryKeyStatus = strawberry.field(resolver=get_recovery_key_status)
