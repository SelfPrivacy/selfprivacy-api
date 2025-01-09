from abc import ABC, abstractmethod
import re
from typing import Optional

from selfprivacy_api.utils import (
    ReadUserData,
    WriteUserData,
    check_if_subdomain_is_taken,
)


class ServiceConfigItem(ABC):
    id: str
    description: str
    widget: str
    type: str
    weight: int

    @abstractmethod
    def get_value(self, service_id):
        pass

    @abstractmethod
    def set_value(self, value, service_id):
        pass

    @abstractmethod
    def validate_value(self, value):
        return True

    def as_dict(self, service_id: str):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "widget": self.widget,
            "value": self.get_value(service_id),
            "weight": self.weight,
        }


class StringServiceConfigItem(ServiceConfigItem):
    def __init__(
        self,
        id: str,
        default_value: str,
        description: str,
        regex: Optional[str] = None,
        widget: Optional[str] = None,
        allow_empty: bool = False,
        weight: int = 50,
    ):
        if widget == "subdomain" and not regex:
            raise ValueError("Subdomain widget requires regex")
        self.id = id
        self.type = "string"
        self.default_value = default_value
        self.description = description
        self.regex = re.compile(regex) if regex else None
        self.widget = widget if widget else "text"
        self.allow_empty = allow_empty
        self.weight = weight

    def get_value(self, service_id):
        with ReadUserData() as user_data:
            if "modules" in user_data and service_id in user_data["modules"]:
                return user_data["modules"][service_id].get(self.id, self.default_value)
            return self.default_value

    def set_value(self, value, service_id):
        if not self.validate_value(value):
            raise ValueError(f"Value {value} is not valid")
        with WriteUserData() as user_data:
            if "modules" not in user_data:
                user_data["modules"] = {}
            if service_id not in user_data["modules"]:
                user_data["modules"][service_id] = {}
            user_data["modules"][service_id][self.id] = value

    def as_dict(self, service_id):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "widget": self.widget,
            "value": self.get_value(service_id),
            "default_value": self.default_value,
            "regex": self.regex.pattern if self.regex else None,
            "weight": self.weight,
        }

    def validate_value(self, value):
        if not isinstance(value, str):
            return False
        if not self.allow_empty and not value:
            return False
        if self.regex and not self.regex.match(value):
            return False
        if self.widget == "subdomain":
            if check_if_subdomain_is_taken(value):
                return False
        return True


class BoolServiceConfigItem(ServiceConfigItem):
    def __init__(
        self,
        id: str,
        default_value: bool,
        description: str,
        widget: Optional[str] = None,
        weight: int = 50,
    ):
        self.id = id
        self.type = "bool"
        self.default_value = default_value
        self.description = description
        self.widget = widget if widget else "switch"
        self.weight = weight

    def get_value(self, service_id):
        with ReadUserData() as user_data:
            if "modules" in user_data and service_id in user_data["modules"]:
                return user_data["modules"][service_id].get(self.id, self.default_value)
            return self.default_value

    def set_value(self, value, service_id):
        if not self.validate_value(value):
            raise ValueError(f"Value {value} is not a boolean")
        with WriteUserData() as user_data:
            if "modules" not in user_data:
                user_data["modules"] = {}
            if service_id not in user_data["modules"]:
                user_data["modules"][service_id] = {}
            user_data["modules"][service_id][self.id] = value

    def as_dict(self, service_id):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "widget": self.widget,
            "value": self.get_value(service_id),
            "default_value": self.default_value,
            "weight": self.weight,
        }

    def validate_value(self, value):
        return isinstance(value, bool)


class EnumServiceConfigItem(ServiceConfigItem):
    def __init__(
        self,
        id: str,
        default_value: str,
        description: str,
        options: list[str],
        widget: Optional[str] = None,
        weight: int = 50,
    ):
        self.id = id
        self.type = "enum"
        self.default_value = default_value
        self.description = description
        self.options = options
        self.widget = widget if widget else "select"
        self.weight = weight

    def get_value(self, service_id):
        with ReadUserData() as user_data:
            if "modules" in user_data and service_id in user_data["modules"]:
                return user_data["modules"][service_id].get(self.id, self.default_value)
            return self.default_value

    def set_value(self, value, service_id):
        if not self.validate_value(value):
            raise ValueError(f"Value {value} is not in options")
        with WriteUserData() as user_data:
            if "modules" not in user_data:
                user_data["modules"] = {}
            if service_id not in user_data["modules"]:
                user_data["modules"][service_id] = {}
            user_data["modules"][service_id][self.id] = value

    def as_dict(self, service_id):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "widget": self.widget,
            "value": self.get_value(service_id),
            "default_value": self.default_value,
            "options": self.options,
            "weight": self.weight,
        }

    def validate_value(self, value):
        if not isinstance(value, str):
            return False
        return value in self.options


# TODO: unused for now
class IntServiceConfigItem(ServiceConfigItem):
    def __init__(
        self,
        id: str,
        default_value: int,
        description: str,
        widget: Optional[str] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        weight: int = 50,
    ) -> None:
        self.id = id
        self.type = "int"
        self.default_value = default_value
        self.description = description
        self.widget = widget if widget else "number"
        self.min_value = min_value
        self.max_value = max_value
        self.weight = weight

    def get_value(self, service_id):
        with ReadUserData() as user_data:
            if "modules" in user_data and service_id in user_data["modules"]:
                return user_data["modules"][service_id].get(self.id, self.default_value)
            return self.default_value

    def set_value(self, value, service_id):
        if not self.validate_value(value):
            raise ValueError(f"Value {value} is not valid")
        with WriteUserData() as user_data:
            if "modules" not in user_data:
                user_data["modules"] = {}
            if service_id not in user_data["modules"]:
                user_data["modules"][service_id] = {}
            user_data["modules"][service_id][self.id] = value

    def as_dict(self, service_id):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "widget": self.widget,
            "value": self.get_value(service_id),
            "default_value": self.default_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "weight": self.weight,
        }

    def validate_value(self, value):
        if not isinstance(value, int):
            return False
        return (self.min_value is None or value >= self.min_value) and (
            self.max_value is None or value <= self.max_value
        )
