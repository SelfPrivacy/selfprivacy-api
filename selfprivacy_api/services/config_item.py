from abc import ABC, abstractmethod
import re
from typing import Optional


class ConfigItem(ABC):
    id: str
    description: str
    widget: str
    type: str

    @abstractmethod
    def get_value(self, service_options):
        pass

    @abstractmethod
    def set_value(self, value, service_options):
        pass

    def as_dict(self, service_options):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "widget": self.widget,
            "value": self.get_value(service_options),
        }


class StringConfigItem(ConfigItem):
    def __init__(
        self,
        id: str,
        default_value: str,
        description: str,
        regex: Optional[str] = None,
        widget: Optional[str] = None,
    ):
        self.id = id
        self.type = "string"
        self.default_value = default_value
        self.description = description
        self.regex = re.compile(regex) if regex else None
        self.widget = widget if widget else "text"

    def get_value(self, service_options):
        return service_options.get(self.id, self.default_value)

    def set_value(self, value, service_options):
        if self.regex and not self.regex.match(value):
            raise ValueError(f"Value {value} does not match regex {self.regex}")
        service_options[self.id] = value


class BoolConfigItem(ConfigItem):
    def __init__(
        self,
        id: str,
        default_value: bool,
        description: str,
        widget: Optional[str] = None,
    ):
        self.id = id
        self.type = "bool"
        self.default_value = default_value
        self.description = description
        self.widget = widget if widget else "switch"

    def get_value(self, service_options):
        return service_options.get(self.id, self.default_value)

    def set_value(self, value, service_options):
        service_options[self.id] = value


class EnumConfigItem(ConfigItem):
    def __init__(
        self,
        id: str,
        default_value: str,
        description: str,
        options: list[str],
        widget: Optional[str] = None,
    ):
        self.id = id
        self.type = "enum"
        self.default_value = default_value
        self.description = description
        self.options = options
        self.widget = widget if widget else "select"

    def get_value(self, service_options):
        return service_options.get(self.id, self.default_value)

    def set_value(self, value, service_options):
        if value not in self.options:
            raise ValueError(f"Value {value} not in options {self.options}")
        service_options[self.id] = value
