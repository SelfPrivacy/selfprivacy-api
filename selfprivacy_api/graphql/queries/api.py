"""API access status"""
# pylint: disable=too-few-public-methods
import datetime
import typing
import strawberry

from selfprivacy_api.resolve_functions.api import get_api_version

@strawberry.type
class ApiDevice:
    name: str
    creation_date: datetime.datetime
    is_caller: bool

@strawberry.type
class ApiRecoveryKeyStatus:
    exists: bool
    valid: bool
    creation_date: datetime.datetime
    expiration_date: typing.Optional[datetime.datetime]
    uses_left: typing.Optional[int]

@strawberry.type
class Api:
    version: str = strawberry.field(resolver=get_api_version)
    devices: typing.List[ApiDevice]
    recovery_key: ApiRecoveryKeyStatus
