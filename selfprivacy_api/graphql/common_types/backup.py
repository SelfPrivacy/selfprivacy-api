"""Backup"""
# pylint: disable=too-few-public-methods
import strawberry
from enum import Enum
from pydantic import BaseModel


@strawberry.enum
class RestoreStrategy(Enum):
    INPLACE = "INPLACE"
    DOWNLOAD_VERIFY_OVERWRITE = "DOWNLOAD_VERIFY_OVERWRITE"


@strawberry.enum
class BackupReason(Enum):
    EXPLICIT = "EXPLICIT"
    AUTO = "AUTO"
    PRE_RESTORE = "PRE_RESTORE"


class _AutobackupQuotas(BaseModel):
    daily: int
    weekly: int
    monthly: int
    yearly: int
    total: int


@strawberry.experimental.pydantic.type(model=_AutobackupQuotas, all_fields=True)
class AutobackupQuotas:
    pass


@strawberry.experimental.pydantic.input(model=_AutobackupQuotas, all_fields=True)
class AutobackupQuotasInput:
    pass
