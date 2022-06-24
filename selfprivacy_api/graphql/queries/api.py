"""API access status"""
# pylint: disable=too-few-public-methods
import datetime
import typing
import strawberry

from selfprivacy_api.resolvers.api import get_api_version, get_devices, get_recovery_key_status

@strawberry.type
class ApiDevice:
    """A single device with SelfPrivacy app installed"""
    name: str
    creation_date: datetime.datetime
    is_caller: bool

@strawberry.type
class ApiRecoveryKeyStatus:
    """Recovery key status"""
    exists: bool
    valid: bool
    creation_date: typing.Optional[datetime.datetime]
    expiration_date: typing.Optional[datetime.datetime]
    uses_left: typing.Optional[int]

@strawberry.type
class Api:
    """API access status"""
    version: str = strawberry.field(resolver=get_api_version)
    devices: typing.List[ApiDevice] = strawberry.field(resolver=get_devices)
    recovery_key: ApiRecoveryKeyStatus = strawberry.field(resolver=get_recovery_key_status)
