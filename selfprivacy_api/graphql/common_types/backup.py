"""Backup"""
# pylint: disable=too-few-public-methods
import strawberry
from enum import Enum


@strawberry.enum
class RestoreStrategy(Enum):
    INPLACE = "INPLACE"
    DOWNLOAD_VERIFY_OVERWRITE = "DOWNLOAD_VERIFY_OVERWRITE"
