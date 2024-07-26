"""Backup"""

# pylint: disable=too-few-public-methods
from enum import Enum
import strawberry
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
    last: int
    daily: int
    weekly: int
    monthly: int
    yearly: int


@strawberry.experimental.pydantic.type(model=_AutobackupQuotas, all_fields=True)
class AutobackupQuotas:
    pass


@strawberry.experimental.pydantic.input(model=_AutobackupQuotas, all_fields=True)
class AutobackupQuotasInput:
    pass
