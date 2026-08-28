from selfprivacy_api.utils import ReadUserData, WriteUserData
from tests.test_graphql.common import (
    assert_empty,
    assert_errorcode,
    assert_ok,
    get_data,
)

OPEN_TELEMETRY_FIELDS = """
enable
endpoint
uploadSystemLogs
uploadSystemMetrics
headerNames
memoryTracingEnabled
"""

API_OPEN_TELEMETRY_QUERY = f"""
query OpenTelemetrySettings {{
  system {{
    settings {{
      openTelemetry {{
        {OPEN_TELEMETRY_FIELDS}
      }}
    }}
  }}
}}
"""

API_CHANGE_OPEN_TELEMETRY_SETTINGS = f"""
mutation ChangeOpenTelemetrySettings($settings: OpenTelemetrySettingsInput!) {{
  system {{
    changeOpenTelemetrySettings(settings: $settings) {{
      success
      message
      code
      settings {{
        {OPEN_TELEMETRY_FIELDS}
      }}
    }}
  }}
}}
"""


def open_telemetry_settings(response):
    return get_data(response)["system"]["settings"]["openTelemetry"]


def change_open_telemetry_settings(client, settings):
    response = client.post(
        "/graphql",
        json={
            "query": API_CHANGE_OPEN_TELEMETRY_SETTINGS,
            "variables": {"settings": settings},
        },
    )
    return get_data(response)["system"]["changeOpenTelemetrySettings"]


def test_open_telemetry_query_requires_authentication(client, generic_userdata):
    response = client.post(
        "/graphql",
        json={"query": API_OPEN_TELEMETRY_QUERY},
    )

    assert_empty(response)


def test_open_telemetry_query_returns_defaults_and_runtime_memory_state(
    authorized_client, generic_userdata, mocker
):
    mocker.patch(
        "selfprivacy_api.actions.otel.tracemalloc.is_tracing",
        return_value=True,
    )

    settings = open_telemetry_settings(
        authorized_client.post(
            "/graphql",
            json={"query": API_OPEN_TELEMETRY_QUERY},
        )
    )

    assert settings == {
        "enable": False,
        "endpoint": None,
        "uploadSystemLogs": True,
        "uploadSystemMetrics": True,
        "headerNames": [],
        "memoryTracingEnabled": True,
    }


def test_open_telemetry_query_returns_only_sorted_header_names(
    authorized_client, generic_userdata
):
    with WriteUserData() as user_data:
        user_data["telemetry"] = {
            "enable": True,
            "endpoint": "http://legacy.example.test:4317",
            "uploadSystemLogs": False,
            "uploadSystemMetrics": True,
            "headers": {
                "X-Second": "not-returned",
                "Authorization": "also-not-returned",
            },
        }

    settings = open_telemetry_settings(
        authorized_client.post(
            "/graphql",
            json={"query": API_OPEN_TELEMETRY_QUERY},
        )
    )

    assert settings["endpoint"] == "http://legacy.example.test:4317"
    assert settings["headerNames"] == ["authorization", "x-second"]
    assert "headers" not in settings


def test_change_open_telemetry_settings_requires_authentication(
    client, generic_userdata
):
    response = client.post(
        "/graphql",
        json={
            "query": API_CHANGE_OPEN_TELEMETRY_SETTINGS,
            "variables": {
                "settings": {
                    "enable": False,
                    "endpoint": None,
                    "uploadSystemLogs": True,
                    "uploadSystemMetrics": True,
                }
            },
        },
    )

    assert_empty(response)


def test_change_open_telemetry_settings_persists_without_rebuild(
    authorized_client, generic_userdata, mocker
):
    rebuild = mocker.patch("selfprivacy_api.actions.system.rebuild_system")

    result = change_open_telemetry_settings(
        authorized_client,
        {
            "enable": True,
            "endpoint": "https://collector.example.test:4317",
            "uploadSystemLogs": False,
            "uploadSystemMetrics": True,
            "headers": [
                {"name": "Authorization", "value": "token"},
                {"name": "X-Empty", "value": ""},
            ],
        },
    )

    assert_ok(result)
    assert result["settings"] == {
        "enable": True,
        "endpoint": "https://collector.example.test:4317",
        "uploadSystemLogs": False,
        "uploadSystemMetrics": True,
        "headerNames": ["authorization", "x-empty"],
        "memoryTracingEnabled": False,
    }
    with ReadUserData() as user_data:
        assert user_data["telemetry"]["headers"] == {
            "authorization": "token",
            "x-empty": "",
        }
    rebuild.assert_not_called()


def test_change_open_telemetry_settings_patches_headers(
    authorized_client, generic_userdata
):
    with WriteUserData() as user_data:
        user_data["telemetry"] = {
            "headers": {
                "authorization": "old-token",
                "x-remove": "old-value",
                "x-preserve": "preserved-value",
            }
        }

    result = change_open_telemetry_settings(
        authorized_client,
        {
            "enable": False,
            "endpoint": None,
            "uploadSystemLogs": True,
            "uploadSystemMetrics": False,
            "headers": [
                {"name": "Authorization", "value": "new-token"},
                {"name": "X-Remove", "value": None},
            ],
        },
    )

    assert_ok(result)
    assert result["settings"]["headerNames"] == [
        "authorization",
        "x-preserve",
    ]
    with ReadUserData() as user_data:
        assert user_data["telemetry"]["headers"] == {
            "authorization": "new-token",
            "x-preserve": "preserved-value",
        }


def test_change_open_telemetry_settings_rejects_invalid_input_atomically(
    authorized_client, generic_userdata
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

    result = change_open_telemetry_settings(
        authorized_client,
        {
            "enable": True,
            "endpoint": "http://collector.example.test:4317",
            "uploadSystemLogs": False,
            "uploadSystemMetrics": False,
            "headers": [{"name": "x-new", "value": "new-value"}],
        },
    )

    assert_errorcode(result, 400)
    assert result["settings"]["endpoint"] is None
    assert result["settings"]["headerNames"] == ["x-existing"]
    with ReadUserData() as user_data:
        assert user_data["telemetry"] == original
