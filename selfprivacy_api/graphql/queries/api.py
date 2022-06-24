"""API access status"""
import datetime
import string
import typing
import strawberry

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
    version: str
    devices: typing.List[ApiDevice]
    recovery_key: ApiRecoveryKeyStatus
