"""Common types and enums used by different types of queries."""

from enum import Enum
import datetime
import typing
import strawberry


@strawberry.enum
class Severity(Enum):
    """
    Severity of an alert.
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


@strawberry.type
class Alert:
    """
    Alert type.
    """

    severity: Severity
    title: str
    message: str
    timestamp: typing.Optional[datetime.datetime]
