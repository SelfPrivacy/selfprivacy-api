import pytest

from selfprivacy_api.actions.otel import (
    get_open_telemetry_settings,
    set_open_telemetry_settings,
)
from selfprivacy_api.utils import ReadUserData, WriteUserData


def test_get_open_telemetry_settings_uses_defaults(generic_userdata, mocker):
    mocker.patch(
        "selfprivacy_api.actions.otel.tracemalloc.is_tracing",
        return_value=True,
    )

    settings = get_open_telemetry_settings()

    assert settings.enable is False
    assert settings.endpoint is None
    assert settings.upload_system_logs is True
    assert settings.upload_system_metrics is True
    assert settings.headers == {}
    assert settings.memory_tracing_enabled is True


def test_get_open_telemetry_settings_reads_legacy_http_endpoint(
    generic_userdata, mocker
):
    mocker.patch(
        "selfprivacy_api.actions.otel.tracemalloc.is_tracing",
        return_value=False,
    )
    with WriteUserData() as user_data:
        user_data["telemetry"] = {
            "enable": True,
            "endpoint": "http://collector.example.test:4317",
            "uploadSystemLogs": False,
            "uploadSystemMetrics": False,
            "headers": {"Authorization": "token"},
        }

    settings = get_open_telemetry_settings()

    assert settings.enable is True
    assert settings.endpoint == "http://collector.example.test:4317"
    assert settings.upload_system_logs is False
    assert settings.upload_system_metrics is False
    assert settings.headers == {"authorization": "token"}
    assert settings.memory_tracing_enabled is False


def test_set_open_telemetry_settings_replaces_values_and_updates_headers(
    generic_userdata,
):
    with WriteUserData() as user_data:
        user_data["telemetry"] = {
            "headers": {
                "Authorization": "old-token",
                "x-remove": "old-value",
            }
        }

    settings = set_open_telemetry_settings(
        enable=True,
        endpoint="https://collector.example.test:4317",
        upload_system_logs=False,
        upload_system_metrics=True,
        header_updates=[
            ("AUTHORIZATION", "new-token"),
            ("x-remove", None),
            ("x-empty", ""),
        ],
    )

    assert settings.enable is True
    assert settings.endpoint == "https://collector.example.test:4317"
    assert settings.upload_system_logs is False
    assert settings.upload_system_metrics is True
    assert settings.headers == {
        "authorization": "new-token",
        "x-empty": "",
    }
    with ReadUserData() as user_data:
        assert user_data["telemetry"] == {
            "enable": True,
            "endpoint": "https://collector.example.test:4317",
            "uploadSystemLogs": False,
            "uploadSystemMetrics": True,
            "headers": {
                "authorization": "new-token",
                "x-empty": "",
            },
        }


def test_set_open_telemetry_settings_preserves_headers_when_updates_are_absent(
    generic_userdata,
):
    with WriteUserData() as user_data:
        user_data["telemetry"] = {"headers": {"x-token": "value"}}

    settings = set_open_telemetry_settings(
        enable=False,
        endpoint=None,
        upload_system_logs=True,
        upload_system_metrics=False,
    )

    assert settings.headers == {"x-token": "value"}


@pytest.mark.parametrize("telemetry", [None, False, [], ""])
def test_open_telemetry_actions_reject_invalid_settings_objects(
    generic_userdata, telemetry
):
    with WriteUserData() as user_data:
        user_data["telemetry"] = telemetry

    with pytest.raises(ValueError):
        get_open_telemetry_settings()

    with pytest.raises(ValueError):
        set_open_telemetry_settings(
            enable=False,
            endpoint=None,
            upload_system_logs=True,
            upload_system_metrics=True,
        )


@pytest.mark.parametrize("headers", [None, False, [], ""])
def test_open_telemetry_actions_reject_invalid_header_objects(
    generic_userdata, headers
):
    with WriteUserData() as user_data:
        user_data["telemetry"] = {"headers": headers}

    with pytest.raises(ValueError):
        get_open_telemetry_settings()

    with pytest.raises(ValueError):
        set_open_telemetry_settings(
            enable=False,
            endpoint=None,
            upload_system_logs=True,
            upload_system_metrics=True,
        )


@pytest.mark.parametrize(
    "endpoint",
    [
        None,
        "http://collector.example.test:4317",
        "https://collector.example.test",
        "https://collector.example.test:4317/",
        "https://user@collector.example.test:4317",
        "https://collector.example.test:4317?tenant=test",
        "https://collector.example.test:4317#fragment",
        "https://collector.example.test:not-a-port",
        "https://bad host:4317",
    ],
)
def test_set_open_telemetry_settings_rejects_invalid_enabled_endpoint(
    generic_userdata, endpoint
):
    with pytest.raises(ValueError):
        set_open_telemetry_settings(
            enable=True,
            endpoint=endpoint,
            upload_system_logs=True,
            upload_system_metrics=True,
        )


@pytest.mark.parametrize(
    "header_updates",
    [
        [("invalid header", "value")],
        [("x-token", "line one\nline two")],
        [("X-Token", "first"), ("x-token", "second")],
    ],
)
def test_set_open_telemetry_settings_rejects_invalid_headers_atomically(
    generic_userdata, header_updates
):
    original = {
        "enable": False,
        "endpoint": None,
        "uploadSystemLogs": True,
        "uploadSystemMetrics": True,
        "headers": {"x-existing": "value"},
    }
    with WriteUserData() as user_data:
        user_data["telemetry"] = original.copy()

    with pytest.raises(ValueError):
        set_open_telemetry_settings(
            enable=True,
            endpoint="https://collector.example.test:4317",
            upload_system_logs=False,
            upload_system_metrics=False,
            header_updates=header_updates,
        )

    with ReadUserData() as user_data:
        assert user_data["telemetry"] == original
