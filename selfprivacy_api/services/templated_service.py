"""A Service implementation that loads all needed data from a JSON file"""

import base64
from enum import Enum
import json
import subprocess
from typing import List, Optional
from os import path
from os.path import join, exists

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from selfprivacy_api.models.services import ServiceDnsRecord, ServiceStatus
from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.services.generic_size_counter import get_storage_usage
from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.services.service import Service
from selfprivacy_api.utils import ReadUserData, WriteUserData, get_domain
from selfprivacy_api.services.config_item import (
    ServiceConfigItem,
    StringServiceConfigItem,
    BoolServiceConfigItem,
    EnumServiceConfigItem,
    IntServiceConfigItem,
)
from selfprivacy_api.utils.block_devices import BlockDevice, BlockDevices
from selfprivacy_api.utils.systemd import get_service_status_from_several_units

"""The structure of the JSON used:
```json
{
  "configPathsNeeded": [
    [
      "selfprivacy",
      "domain"
    ],
    [
      "selfprivacy",
      "useBinds"
    ],
    [
      "selfprivacy",
      "modules",
      "gitea"
    ]
  ],
  "meta": {
    "backupDescription": "Git repositories, database and user data.",
    "description": "Forgejo is a Git forge.",
    "folders": [
      "/var/lib/gitea"
    ],
    "homepage": "https://forgejo.org",
    "id": "gitea",
    "isMovable": true,
    "isRequired": false,
    "license": [
      {
        "deprecated": false,
        "free": true,
        "fullName": "GNU General Public License v3.0 or later",
        "redistributable": true,
        "shortName": "gpl3Plus",
        "spdxId": "GPL-3.0-or-later",
        "url": "https://spdx.org/licenses/GPL-3.0-or-later.html"
      }
    ],
    "name": "Forgejo",
    "sourcePage": "https://codeberg.org/forgejo/forgejo",
    "spModuleVersion": 1,
    "supportLevel": "normal",
    "svgIcon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n<path d=\"M2.60007 10.5899L8.38007 4.79995L10.0701 6.49995C9.83007 7.34995 10.2201 8.27995 11.0001 8.72995V14.2699C10.4001 14.6099 10.0001 15.2599 10.0001 15.9999C10.0001 16.5304 10.2108 17.0391 10.5859 17.4142C10.9609 17.7892 11.4696 17.9999 12.0001 17.9999C12.5305 17.9999 13.0392 17.7892 13.4143 17.4142C13.7894 17.0391 14.0001 16.5304 14.0001 15.9999C14.0001 15.2599 13.6001 14.6099 13.0001 14.2699V9.40995L15.0701 11.4999C15.0001 11.6499 15.0001 11.8199 15.0001 11.9999C15.0001 12.5304 15.2108 13.0391 15.5859 13.4142C15.9609 13.7892 16.4696 13.9999 17.0001 13.9999C17.5305 13.9999 18.0392 13.7892 18.4143 13.4142C18.7894 13.0391 19.0001 12.5304 19.0001 11.9999C19.0001 11.4695 18.7894 10.9608 18.4143 10.5857C18.0392 10.2107 17.5305 9.99995 17.0001 9.99995C16.8201 9.99995 16.6501 9.99995 16.5001 10.0699L13.9301 7.49995C14.1901 6.56995 13.7101 5.54995 12.7801 5.15995C12.3501 4.99995 11.9001 4.95995 11.5001 5.06995L9.80007 3.37995L10.5901 2.59995C11.3701 1.80995 12.6301 1.80995 13.4101 2.59995L21.4001 10.5899C22.1901 11.3699 22.1901 12.6299 21.4001 13.4099L13.4101 21.3999C12.6301 22.1899 11.3701 22.1899 10.5901 21.3999L2.60007 13.4099C1.81007 12.6299 1.81007 11.3699 2.60007 10.5899Z\" fill=\"black\"/>\n</svg>\n",
    "systemdServices": [
      "forgejo.service"
    ]
  },
  "options": {
    "appName": {
      "default": "SelfPrivacy git Service",
      "description": "The name displayed in the web interface",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "appName"
      ],
      "meta": {
        "type": "string"
      },
      "name": "appName"
    },
    "defaultTheme": {
      "default": "forgejo-auto",
      "description": "Default theme",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "defaultTheme"
      ],
      "meta": {
        "options": [
          "forgejo-auto",
          "forgejo-light",
          "forgejo-dark",
          "gitea-auto",
          "gitea-light",
          "gitea-dark"
        ],
        "type": "enum"
      },
      "name": "defaultTheme"
    },
    "disableRegistration": {
      "default": false,
      "description": "Disable registration of new users",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "disableRegistration"
      ],
      "meta": {
        "type": "bool"
      },
      "name": "disableRegistration"
    },
    "enable": {
      "default": false,
      "description": "Enable Forgejo",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "enable"
      ],
      "meta": {
        "type": "enable"
      },
      "name": "enable"
    },
    "enableLfs": {
      "default": true,
      "description": "Enable Git LFS",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "enableLfs"
      ],
      "meta": {
        "type": "bool"
      },
      "name": "enableLfs"
    },
    "forcePrivate": {
      "default": false,
      "description": "Force all new repositories to be private",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "forcePrivate"
      ],
      "meta": {
        "type": "bool"
      },
      "name": "forcePrivate"
    },
    "location": {
      "default": null,
      "description": "Forgejo location",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "location"
      ],
      "meta": {
        "type": "location"
      },
      "name": "location"
    },
    "requireSigninView": {
      "default": false,
      "description": "Force users to log in to view any page",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "requireSigninView"
      ],
      "meta": {
        "type": "bool"
      },
      "name": "requireSigninView"
    },
    "subdomain": {
      "default": "git",
      "description": "Subdomain",
      "loc": [
        "selfprivacy",
        "modules",
        "gitea",
        "subdomain"
      ],
      "meta": {
        "regex": "[A-Za-z0-9][A-Za-z0-9-]{0,61}[A-Za-z0-9]",
        "type": "string",
        "widget": "subdomain"
      },
      "name": "subdomain"
    }
  }
}

```

Theses files are stored in `/etc/sp-modules` and are named after the service id.
"""

SP_MODULES_DEFENITIONS_PATH = "/etc/sp-modules"


class SupportLevel(Enum):
    """Enum representing the support level of a service."""

    NORMAL = "normal"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
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
        return cls.UNKNOWN


def config_item_from_json(json_data: dict) -> Optional[ServiceConfigItem]:
    """Create a ServiceConfigItem from JSON data."""
    weight = json_data.get("meta", {}).get("weight", 50)
    if json_data["meta"]["type"] == "enable":
        return None
    if json_data["meta"]["type"] == "location":
        return None
    if json_data["meta"]["type"] == "string":
        return StringServiceConfigItem(
            id=json_data["name"],
            default_value=json_data["default"],
            description=json_data["description"],
            regex=json_data["meta"].get("regex"),
            widget=json_data["meta"].get("widget"),
            allow_empty=json_data["meta"].get("allowEmpty", False),
            weight=weight,
        )
    if json_data["meta"]["type"] == "bool":
        return BoolServiceConfigItem(
            id=json_data["name"],
            default_value=json_data["default"],
            description=json_data["description"],
            widget=json_data["meta"].get("widget"),
            weight=weight,
        )
    if json_data["meta"]["type"] == "enum":
        return EnumServiceConfigItem(
            id=json_data["name"],
            default_value=json_data["default"],
            description=json_data["description"],
            options=json_data["meta"]["options"],
            widget=json_data["meta"].get("widget"),
            weight=weight,
        )
    if json_data["meta"]["type"] == "int":
        return IntServiceConfigItem(
            id=json_data["name"],
            default_value=json_data["default"],
            description=json_data["description"],
            widget=json_data["meta"].get("widget"),
            min_value=json_data["meta"].get("minValue"),
            max_value=json_data["meta"].get("maxValue"),
            weight=weight,
        )
    raise ValueError("Unknown config item type")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class License(BaseSchema):
    """Model representing a license."""

    deprecated: bool
    free: bool
    full_name: str
    redistributable: bool
    short_name: str
    spdx_id: str
    url: str


class ServiceMetaData(BaseSchema):
    """Model representing the meta data of a service."""

    id: str
    name: str
    description: str = "No description found!"
    svg_icon: str = ""
    showUrl: bool = True
    primary_subdomain: Optional[str] = None
    is_movable: bool = False
    is_required: bool = False
    can_be_backed_up: bool = True
    backup_description: str = "No backup description found!"
    systemd_services: List[str]
    user: Optional[str] = None
    group: Optional[str] = None
    folders: List[str] = []
    owned_folders: List[OwnedPath] = []
    postgresql_databases: List[str] = []
    license: List[License] = []
    homepage: Optional[str] = None
    source_page: Optional[str] = None
    support_level: SupportLevel = SupportLevel.UNKNOWN


class TemplatedService(Service):
    """Class representing a dynamically loaded service."""

    def __init__(self, service_id: str, source_data: Optional[str] = None) -> None:
        if source_data:
            self.definition_data = json.loads(source_data)
        else:
            # Check if the service exists
            if not path.exists(join(SP_MODULES_DEFENITIONS_PATH, service_id)):
                raise FileNotFoundError(f"Service {service_id} not found")
            # Load the service
            with open(join(SP_MODULES_DEFENITIONS_PATH, service_id)) as file:
                self.definition_data = json.load(file)
        # Check if required fields are present
        if "meta" not in self.definition_data:
            raise ValueError("meta not found in service definition")
        if "options" not in self.definition_data:
            raise ValueError("options not found in service definition")
        # Load the meta data
        self.meta = ServiceMetaData(**self.definition_data["meta"])
        # Load the options
        self.options = self.definition_data["options"]
        # Load the config items
        self.config_items = {}
        for option in self.options.values():
            config_item = config_item_from_json(option)
            if config_item:
                self.config_items[config_item.id] = config_item
        # If it is movable, check for the location option
        if self.meta.is_movable and "location" not in self.options:
            raise ValueError("Service is movable but does not have a location option")
        # Load all subdomains via options with "subdomain" widget
        self.subdomain_options: List[str] = []
        for option in self.options.values():
            if option.get("meta", {}).get("widget") == "subdomain":
                self.subdomain_options.append(option["name"])

    def get_id(self) -> str:
        return self.meta.id

    def get_display_name(self) -> str:
        return self.meta.name

    def get_description(self) -> str:
        return self.meta.description

    def get_svg_icon(self) -> str:
        return base64.b64encode(self.meta.svg_icon.encode("utf-8")).decode("utf-8")

    def get_subdomain(self) -> Optional[str]:
        # If there are no subdomain options, return None
        if not self.subdomain_options:
            return None
        # If primary_subdomain is set, try to find it in the options
        if (
            self.meta.primary_subdomain
            and self.meta.primary_subdomain in self.subdomain_options
        ):
            option_name = self.meta.primary_subdomain
        # Otherwise, use the first subdomain option
        else:
            option_name = self.subdomain_options[0]

        # Now, read the value from the userdata
        name = self.get_id()
        with ReadUserData() as user_data:
            if "modules" in user_data:
                if name in user_data["modules"]:
                    if option_name in user_data["modules"][name]:
                        return user_data["modules"][name][option_name]
        # Otherwise, return default value for the option
        return self.options[option_name].get("default")

    def get_subdomains(self) -> List[str]:
        # Return a current subdomain for every subdomain option
        subdomains = []
        with ReadUserData() as user_data:
            for option in self.subdomain_options:
                if "modules" in user_data:
                    if self.get_id() in user_data["modules"]:
                        if option in user_data["modules"][self.get_id()]:
                            subdomains.append(
                                user_data["modules"][self.get_id()][option]
                            )
                            continue
                subdomains.append(self.options[option]["default"])
        return subdomains

    def get_url(self) -> Optional[str]:
        if not self.meta.showUrl:
            return None
        subdomain = self.get_subdomain()
        if not subdomain:
            return None
        return f"https://{subdomain}.{get_domain()}"

    def get_user(self) -> Optional[str]:
        if not self.meta.user:
            return self.get_id()
        return self.meta.user

    def get_group(self) -> Optional[str]:
        if not self.meta.group:
            return self.get_user()
        return self.meta.group

    def is_movable(self) -> bool:
        return self.meta.is_movable

    def is_required(self) -> bool:
        return self.meta.is_required

    def can_be_backed_up(self) -> bool:
        return self.meta.can_be_backed_up

    def get_backup_description(self) -> str:
        return self.meta.backup_description

    def is_enabled(self) -> bool:
        name = self.get_id()
        with ReadUserData() as user_data:
            return user_data.get("modules", {}).get(name, {}).get("enable", False)

    def is_installed(self) -> bool:
        name = self.get_id()
        with FlakeServiceManager() as service_manager:
            return name in service_manager.services

    def get_status(self) -> ServiceStatus:
        if not self.meta.systemd_services:
            return ServiceStatus.INACTIVE
        return get_service_status_from_several_units(self.meta.systemd_services)

    def _set_enable(self, enable: bool):
        name = self.get_id()
        with WriteUserData() as user_data:
            if "modules" not in user_data:
                user_data["modules"] = {}
            if name not in user_data["modules"]:
                user_data["modules"][name] = {}
            user_data["modules"][name]["enable"] = enable

    def enable(self):
        """Enable the service. Usually this means enabling systemd unit."""
        self._set_enable(True)

    def disable(self):
        """Disable the service. Usually this means disabling systemd unit."""
        self._set_enable(False)

    def start(self):
        """Start the systemd units"""
        for unit in self.meta.systemd_services:
            subprocess.run(["systemctl", "start", unit], check=False)

    def stop(self):
        """Stop the systemd units"""
        for unit in self.meta.systemd_services:
            subprocess.run(["systemctl", "stop", unit], check=False)

    def restart(self):
        """Restart the systemd units"""
        for unit in self.meta.systemd_services:
            subprocess.run(["systemctl", "restart", unit], check=False)

    def get_configuration(self) -> dict:
        # If there are no options, return an empty dict
        if not self.config_items:
            return {}
        return {
            key: self.config_items[key].as_dict(self.get_id())
            for key in self.config_items
        }

    def set_configuration(self, config_items):
        for key, value in config_items.items():
            if key not in self.config_items:
                raise ValueError(f"Key {key} is not valid for {self.get_id()}")
            if self.config_items[key].validate_value(value) is False:
                raise ValueError(f"Value {value} is not valid for {key}")
        for key, value in config_items.items():
            self.config_items[key].set_value(
                value,
                self.get_id(),
            )

    def get_storage_usage(self) -> int:
        """
        Calculate the real storage usage of folders occupied by service
        Calculate using pathlib.
        Do not follow symlinks.
        """
        storage_used = 0
        for folder in self.get_folders():
            storage_used += get_storage_usage(folder)
        return storage_used

    def has_folders(self) -> int:
        """
        If there are no folders on disk, moving is noop
        """
        for folder in self.get_folders():
            if exists(folder):
                return True
        return False

    def get_dns_records(self, ip4: str, ip6: Optional[str]) -> List[ServiceDnsRecord]:
        display_name = self.get_display_name()
        subdomains = self.get_subdomains()
        # Generate records for every subdomain
        records: List[ServiceDnsRecord] = []
        for subdomain in subdomains:
            if not subdomain:
                continue
            records.append(
                ServiceDnsRecord(
                    type="A",
                    name=subdomain,
                    content=ip4,
                    ttl=3600,
                    display_name=display_name,
                )
            )
            if ip6:
                records.append(
                    ServiceDnsRecord(
                        type="AAAA",
                        name=subdomain,
                        content=ip6,
                        ttl=3600,
                        display_name=display_name,
                    )
                )
        return records

    def get_drive(self) -> str:
        """
        Get the name of the drive/volume where the service is located.
        Example values are `sda1`, `vda`, `sdb`.
        """
        root_device: str = BlockDevices().get_root_block_device().name
        if not self.is_movable():
            return root_device
        with ReadUserData() as userdata:
            if userdata.get("useBinds", False):
                return (
                    userdata.get("modules", {})
                    .get(self.get_id(), {})
                    .get(
                        "location",
                        root_device,
                    )
                )
            else:
                return root_device

    def get_folders(self) -> List[str]:
        folders = self.meta.folders
        owned_folders = self.meta.owned_folders
        for folder in owned_folders:
            folders.append(folder.path)
        return folders

    def get_owned_folders(self) -> List[OwnedPath]:
        folders = self.meta.folders
        owned_folders = self.meta.owned_folders
        for folder in folders:
            owned_folders.append(self.owned_path(folder))
        return owned_folders

    def set_location(self, volume: BlockDevice):
        """
        Only changes userdata
        """

        service_id = self.get_id()
        with WriteUserData() as user_data:
            if "modules" not in user_data:
                user_data["modules"] = {}
            if service_id not in user_data["modules"]:
                user_data["modules"][service_id] = {}
            user_data["modules"][service_id]["location"] = volume.name

    def owned_path(self, path: str):
        """Default folder ownership"""
        service_name = self.get_display_name()

        try:
            owner = self.get_user()
            if owner is None:
                # TODO: assume root?
                # (if we do not want to do assumptions, maybe not declare user optional?)
                raise LookupError(f"no user for service: {service_name}")
            group = self.get_group()
            if group is None:
                raise LookupError(f"no group for service: {service_name}")
        except Exception as error:
            raise LookupError(
                f"when deciding a bind for folder {path} of service {service_name}, error: {str(error)}"
            )

        return OwnedPath(
            path=path,
            owner=owner,
            group=group,
        )
