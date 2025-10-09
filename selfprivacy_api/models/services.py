import gettext
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from selfprivacy_api.services.owned_path import OwnedPath

_ = gettext.gettext


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ServiceStatus(Enum):
    """Enum for service status"""

    ACTIVE = "ACTIVE"
    RELOADING = "RELOADING"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"
    ACTIVATING = "ACTIVATING"
    DEACTIVATING = "DEACTIVATING"
    OFF = "OFF"


class SupportLevel(Enum):
    """Enum representing the support level of a service."""

    NORMAL = "normal"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    COMMUNITY = "community"
    UNKNOWN = "unknown"

    @classmethod
    def from_str(cls, support_level: str) -> "SupportLevel":
        """Return the SupportLevel from a string."""
        if support_level == "normal":
            return cls.NORMAL
        if support_level == "experimental":
            return cls.EXPERIMENTAL
        if support_level == "deprecated":
            return cls.DEPRECATED
        if support_level == "community":
            return cls.COMMUNITY
        return cls.UNKNOWN


class ServiceDnsRecord(BaseModel):
    type: str
    name: str
    content: str

    ttl: int
    display_name: str
    priority: Optional[int] = None


class License(BaseSchema):
    """Model representing a license."""

    deprecated: bool
    free: bool
    full_name: str
    redistributable: bool
    short_name: str
    spdx_id: Optional[str] = None
    url: Optional[str] = None


class SingleSignOnGroups(BaseSchema):
    """Model representing the groups for Single Sign On."""

    user_group: Optional[str] = None
    admin_group: Optional[str] = None


class ServiceMetaData(BaseSchema):
    """Model representing the meta data of a service."""

    id: str
    name: str
    description: str = _("No description found!")
    svg_icon: str = ""
    showUrl: bool = True
    primary_subdomain: Optional[str] = None
    is_movable: bool = False
    is_required: bool = False
    can_be_backed_up: bool = True
    backup_description: str = _("No backup description found!")
    systemd_services: List[str]
    user: Optional[str] = None
    group: Optional[str] = None
    folders: List[str] = []
    owned_folders: List[OwnedPath] = []
    postgre_databases: List[str] = []
    license: List[License] = []
    homepage: Optional[str] = None
    source_page: Optional[str] = None
    support_level: SupportLevel = SupportLevel.UNKNOWN
    sso: Optional[SingleSignOnGroups] = None
