"""API access status"""
# pylint: disable=too-few-public-methods
import datetime
import typing
import strawberry


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
