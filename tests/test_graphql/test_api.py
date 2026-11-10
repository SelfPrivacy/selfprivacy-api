# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.graphql import mutation_error_fields
from selfprivacy_api.utils.localization import DEFAULT_LOCALE
from tests.common import generate_api_query
from tests.test_graphql.common import assert_original_devices
from tests.test_graphql.test_api_devices import API_DEVICES_QUERY
from tests.test_graphql.test_api_recovery import API_RECOVERY_QUERY
from tests.test_graphql.test_api_version import API_VERSION_QUERY


def test_graphql_get_entire_api_data(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_api_query(
                [API_VERSION_QUERY, API_DEVICES_QUERY, API_RECOVERY_QUERY]
            )
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert "version" in response.json()["data"]["api"]

    devices = response.json()["data"]["api"]["devices"]
    assert devices is not None
    assert_original_devices(devices)

    assert response.json()["data"]["api"]["recoveryKey"] is not None
    assert response.json()["data"]["api"]["recoveryKey"]["exists"] is False
    assert response.json()["data"]["api"]["recoveryKey"]["valid"] is False
    assert response.json()["data"]["api"]["recoveryKey"]["creationDate"] is None
    assert response.json()["data"]["api"]["recoveryKey"]["expirationDate"] is None
    assert response.json()["data"]["api"]["recoveryKey"]["usesLeft"] is None


class DummySelfPrivacyException(AbstractException):
    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return f"some error with locale: {locale}"


def test_mutation_error_fields_correctly_passes_locale(mocker):
    exc = DummySelfPrivacyException(log=False)
    spy = mocker.spy(exc, "get_error_message")

    resp = mutation_error_fields(exc, "es")

    assert resp["success"] == False
    assert resp["message"] == "some error with locale: es"
    assert resp["code"] == 400

    spy.assert_called_once_with(locale="es")


def test_mutation_error_fields_correctly_returns_unknown_exceptions():
    exc = RuntimeError("Something went wrong")

    resp = mutation_error_fields(exc, "es")

    assert resp["success"] == False
    print(resp)
    assert (
        resp["message"].splitlines()[0] == "RuntimeError: Something went wrong: "
    )  # rest is stack trace
    assert resp["code"] == 500
