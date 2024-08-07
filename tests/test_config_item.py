import pytest
from selfprivacy_api.services.config_item import (
    StringServiceConfigItem,
    BoolServiceConfigItem,
    EnumServiceConfigItem,
)
from selfprivacy_api.utils.regex_strings import SUBDOMAIN_REGEX


@pytest.fixture
def service_options():
    return {}


DUMMY_SERVICE = "testservice"


def test_string_service_config_item(dummy_service):
    item = StringServiceConfigItem(
        id="test_string",
        default_value="1337",
        description="Test digits string",
        regex=r"^\d+$",
        widget="text",
        allow_empty=False,
    )
    assert item.get_value(DUMMY_SERVICE) == "1337"
    item.set_value("123", DUMMY_SERVICE)
    assert item.get_value(DUMMY_SERVICE) == "123"
    with pytest.raises(ValueError):
        item.set_value("abc", DUMMY_SERVICE)
    assert item.validate_value("123") is True
    assert item.validate_value("abc") is False
    assert item.validate_value("123abc") is False
    assert item.validate_value("") is False
    assert item.validate_value(None) is False
    assert item.validate_value(123) is False
    assert item.validate_value("123.0") is False
    assert item.validate_value(True) is False


def test_string_service_config_item_allows_empty(dummy_service):
    item = StringServiceConfigItem(
        id="test_string",
        default_value="1337",
        description="Test digits string",
        widget="text",
        allow_empty=True,
    )
    assert item.get_value(DUMMY_SERVICE) == "1337"
    item.set_value("", DUMMY_SERVICE)
    assert item.get_value(DUMMY_SERVICE) == ""
    assert item.validate_value("") is True
    assert item.validate_value(None) is False
    assert item.validate_value(123) is False
    assert item.validate_value("123") is True
    assert item.validate_value("abc") is True
    assert item.validate_value("123abc") is True
    assert item.validate_value("123.0") is True
    assert item.validate_value(True) is False


def test_string_service_config_item_not_allows_empty(dummy_service):
    item = StringServiceConfigItem(
        id="test_string",
        default_value="1337",
        description="Test digits string",
        widget="text",
    )
    assert item.get_value(DUMMY_SERVICE) == "1337"
    with pytest.raises(ValueError):
        item.set_value("", DUMMY_SERVICE)
    assert item.get_value(DUMMY_SERVICE) == "1337"
    assert item.validate_value("") is False
    assert item.validate_value(None) is False
    assert item.validate_value(123) is False
    assert item.validate_value("123") is True
    assert item.validate_value("abc") is True
    assert item.validate_value("123abc") is True
    assert item.validate_value("123.0") is True
    assert item.validate_value(True) is False


def test_bool_service_config_item(dummy_service):
    item = BoolServiceConfigItem(
        id="test_bool",
        default_value=True,
        description="Test bool",
        widget="switch",
    )
    assert item.get_value(DUMMY_SERVICE) is True
    item.set_value(False, DUMMY_SERVICE)
    assert item.get_value(DUMMY_SERVICE) is False
    assert item.validate_value(True) is True
    assert item.validate_value(False) is True
    assert item.validate_value("True") is False
    assert item.validate_value("False") is False
    assert item.validate_value(1) is False
    assert item.validate_value(0) is False
    assert item.validate_value("1") is False


def test_enum_service_config_item(dummy_service):
    item = EnumServiceConfigItem(
        id="test_enum",
        default_value="option1",
        description="Test enum",
        options=["option1", "option2", "option3"],
        widget="select",
    )
    assert item.get_value(DUMMY_SERVICE) == "option1"
    item.set_value("option2", DUMMY_SERVICE)
    assert item.get_value(DUMMY_SERVICE) == "option2"
    with pytest.raises(ValueError):
        item.set_value("option4", DUMMY_SERVICE)
    assert item.validate_value("option1") is True
    assert item.validate_value("option4") is False
    assert item.validate_value("option2") is True
    assert item.validate_value(1) is False
    assert item.validate_value("1") is False
    assert item.validate_value(True) is False


def test_string_service_config_item_subdomain(dummy_service):
    item = StringServiceConfigItem(
        id="test_subdomain",
        default_value="example",
        description="Test subdomain string",
        widget="subdomain",
        allow_empty=False,
        regex=SUBDOMAIN_REGEX,
    )
    assert item.get_value(DUMMY_SERVICE) == "example"
    item.set_value("subdomain", DUMMY_SERVICE)
    assert item.get_value(DUMMY_SERVICE) == "subdomain"
    with pytest.raises(ValueError):
        item.set_value(
            "invalid-subdomain-because-it-is-very-very-very-very-very-very-long",
            DUMMY_SERVICE,
        )
    assert item.validate_value("subdomain") is True
    assert (
        item.validate_value(
            "invalid-subdomain-because-it-is-very-very-very-very-very-very-long"
        )
        is False
    )
    assert item.validate_value("api") is False
    assert item.validate_value("auth") is False
    assert item.validate_value("user") is False
    assert item.validate_value("users") is False
    assert item.validate_value("ntfy") is False
    assert item.validate_value("") is False
    assert item.validate_value(None) is False
    assert item.validate_value(123) is False
    assert item.validate_value("123") is True
    assert item.validate_value("abc") is True
    assert item.validate_value("123abc") is True
    assert item.validate_value("123.0") is False
    assert item.validate_value(True) is False
