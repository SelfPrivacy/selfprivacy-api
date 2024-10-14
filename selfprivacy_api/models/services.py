from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ServiceStatus(Enum):
    """Enum for service status"""

    ACTIVE = "ACTIVE"
    RELOADING = "RELOADING"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"
    ACTIVATING = "ACTIVATING"
    DEACTIVATING = "DEACTIVATING"
    OFF = "OFF"


class ServiceDnsRecord(BaseModel):
    type: str
    name: str
    content: str

    ttl: int
    display_name: str
    priority: Optional[int] = None
