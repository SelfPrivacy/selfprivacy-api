# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import datetime
import pytest

from tests.conftest import TOKENS_FILE_CONTENTS
from tests.common import (
    RECOVERY_KEY_VALIDATION_DATETIME,
    DEVICE_KEY_VALIDATION_DATETIME,
    NearFuture,
)

DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S.%fZ",
    "%Y-%m-%d %H:%M:%S.%f",
]


def assert_original(client):
    new_tokens = rest_get_tokens_info(client)

    for token in TOKENS_FILE_CONTENTS["tokens"]:
        assert_token_valid(client, token["token"])
        for new_token in new_tokens:
            if new_token["name"] == token["name"]:
                assert (
                    datetime.datetime.fromisoformat(new_token["date"]) == token["date"]
                )
    assert_no_recovery(client)


def assert_token_valid(client, token):
    client.headers.update({"Authorization": "Bearer " + token})
    assert rest_get_tokens_info(client) is not None


def rest_get_tokens_info(client):
    response = client.get("/auth/tokens")
    assert response.status_code == 200
    return response.json()


def rest_try_authorize_new_device(client, token, device_name):
    response = client.post(
        "/auth/new_device/authorize",
        json={
            "token": token,
            "device": device_name,
        },
    )
    return response


def rest_make_recovery_token(client, expires_at=None, timeformat=None, uses=None):
    json = {}

    if expires_at is not None:
        assert timeformat is not None
        expires_at_str = expires_at.strftime(timeformat)
        json["expiration"] = expires_at_str

    if uses is not None:
        json["uses"] = uses

    if json == {}:
        response = client.post("/auth/recovery_token")
    else:
        response = client.post(
            "/auth/recovery_token",
            json=json,
        )

    assert response.status_code == 200
    assert "token" in response.json()
    return response.json()["token"]


def rest_get_recovery_status(client):
    response = client.get("/auth/recovery_token")
    assert response.status_code == 200
    return response.json()


def rest_get_recovery_date(client):
    status = rest_get_recovery_status(client)
    assert "date" in status
    return status["date"]


def assert_recovery_recent(time_generated):
    assert (
        datetime.datetime.strptime(time_generated, "%Y-%m-%dT%H:%M:%S.%f")
        - datetime.timedelta(seconds=5)
        < datetime.datetime.now()
    )


def assert_no_recovery(client):
    assert not rest_get_recovery_status(client)["exists"]


def rest_recover_with_mnemonic(client, mnemonic_token, device_name):
    recovery_response = client.post(
        "/auth/recovery_token/use",
        json={"token": mnemonic_token, "device": device_name},
    )
    assert recovery_response.status_code == 200
    new_token = recovery_response.json()["token"]
    assert_token_valid(client, new_token)
    return new_token


# Tokens


def test_get_tokens_info(authorized_client, tokens_file):
    assert rest_get_tokens_info(authorized_client) == [
        {"name": "test_token", "date": "2022-01-14T08:31:10.789314", "is_caller": True},
        {
            "name": "test_token2",
            "date": "2022-01-14T08:31:10.789314",
            "is_caller": False,
        },
    ]


def test_get_tokens_unauthorized(client, tokens_file):
    response = client.get("/auth/tokens")
    assert response.status_code == 401


def test_delete_token_unauthorized(client, authorized_client, tokens_file):
    response = client.delete("/auth/tokens")
    assert response.status_code == 401
    assert_original(authorized_client)


def test_delete_token(authorized_client, tokens_file):
    response = authorized_client.delete(
        "/auth/tokens", json={"token_name": "test_token2"}
    )
    assert response.status_code == 200
    assert rest_get_tokens_info(authorized_client) == [
        {"name": "test_token", "date": "2022-01-14T08:31:10.789314", "is_caller": True}
    ]


def test_delete_self_token(authorized_client, tokens_file):
    response = authorized_client.delete(
        "/auth/tokens", json={"token_name": "test_token"}
    )
    assert response.status_code == 400
    assert_original(authorized_client)


def test_delete_nonexistent_token(authorized_client, tokens_file):
    response = authorized_client.delete(
        "/auth/tokens", json={"token_name": "test_token3"}
    )
    assert response.status_code == 404
    assert_original(authorized_client)


def test_refresh_token_unauthorized(client, authorized_client, tokens_file):
    response = client.post("/auth/tokens")
    assert response.status_code == 401
    assert_original(authorized_client)


def test_refresh_token(authorized_client, tokens_file):
    response = authorized_client.post("/auth/tokens")
    assert response.status_code == 200
    new_token = response.json()["token"]
    assert_token_valid(authorized_client, new_token)


# New device


def test_get_new_device_auth_token_unauthorized(client, authorized_client, tokens_file):
    response = client.post("/auth/new_device")
    assert response.status_code == 401
    assert "token" not in response.json()
    assert "detail" in response.json()
    # We only can check existence of a token we know.


def test_get_and_delete_new_device_token(client, authorized_client, tokens_file):
    token = rest_get_new_device_token(authorized_client)
    response = authorized_client.delete("/auth/new_device", json={"token": token})
    assert response.status_code == 200
    assert rest_try_authorize_new_device(client, token, "new_device").status_code == 404


def test_delete_token_unauthenticated(client, authorized_client, tokens_file):
    token = rest_get_new_device_token(authorized_client)
    response = client.delete("/auth/new_device", json={"token": token})
    assert response.status_code == 401
    assert rest_try_authorize_new_device(client, token, "new_device").status_code == 200


def rest_get_new_device_token(client):
    response = client.post("/auth/new_device")
    assert response.status_code == 200
    assert "token" in response.json()
    return response.json()["token"]


def test_get_and_authorize_new_device(client, authorized_client, tokens_file):
    token = rest_get_new_device_token(authorized_client)
    response = rest_try_authorize_new_device(client, token, "new_device")
    assert response.status_code == 200
    assert_token_valid(authorized_client, response.json()["token"])


def test_authorize_new_device_with_invalid_token(
    client, authorized_client, tokens_file
):
    response = rest_try_authorize_new_device(client, "invalid_token", "new_device")
    assert response.status_code == 404
    assert_original(authorized_client)


def test_get_and_authorize_used_token(client, authorized_client, tokens_file):
    token_to_be_used_2_times = rest_get_new_device_token(authorized_client)
    response = rest_try_authorize_new_device(
        client, token_to_be_used_2_times, "new_device"
    )
    assert response.status_code == 200
    assert_token_valid(authorized_client, response.json()["token"])

    response = rest_try_authorize_new_device(
        client, token_to_be_used_2_times, "new_device"
    )
    assert response.status_code == 404


def test_get_and_authorize_token_after_12_minutes(
    client, authorized_client, tokens_file, mocker
):
    token = rest_get_new_device_token(authorized_client)

    # TARDIS sounds
    mock = mocker.patch(DEVICE_KEY_VALIDATION_DATETIME, NearFuture)

    response = rest_try_authorize_new_device(client, token, "new_device")
    assert response.status_code == 404
    assert_original(authorized_client)


def test_authorize_without_token(client, authorized_client, tokens_file):
    response = client.post(
        "/auth/new_device/authorize",
        json={"device": "new_device"},
    )
    assert response.status_code == 422
    assert_original(authorized_client)


# Recovery tokens
# GET /auth/recovery_token returns token status
#  - if token is valid, returns 200 and token status
#   - token status:
#     - exists (boolean)
#     - valid (boolean)
#     - date (string)
#     - expiration (string)
#     - uses_left (int)
#  - if token is invalid, returns 400 and empty body
# POST /auth/recovery_token generates a new token
#  has two optional parameters:
#   - expiration (string in datetime format)
#   - uses_left (int)
# POST /auth/recovery_token/use uses the token
# required arguments:
#   - token (string)
#   - device (string)
#  - if token is valid, returns 200 and token
#  - if token is invalid, returns 404
#  - if request is invalid, returns 400


def test_get_recovery_token_status_unauthorized(client, authorized_client, tokens_file):
    response = client.get("/auth/recovery_token")
    assert response.status_code == 401
    assert_original(authorized_client)


def test_get_recovery_token_when_none_exists(authorized_client, tokens_file):
    response = authorized_client.get("/auth/recovery_token")
    assert response.status_code == 200
    assert response.json() == {
        "exists": False,
        "valid": False,
        "date": None,
        "expiration": None,
        "uses_left": None,
    }
    assert_original(authorized_client)


def test_generate_recovery_token(authorized_client, client, tokens_file):
    # Generate token without expiration and uses_left
    mnemonic_token = rest_make_recovery_token(authorized_client)

    time_generated = rest_get_recovery_date(authorized_client)
    assert_recovery_recent(time_generated)

    assert rest_get_recovery_status(authorized_client) == {
        "exists": True,
        "valid": True,
        "date": time_generated,
        "expiration": None,
        "uses_left": None,
    }

    rest_recover_with_mnemonic(client, mnemonic_token, "recover_device")
    # And again
    rest_recover_with_mnemonic(client, mnemonic_token, "recover_device2")


@pytest.mark.parametrize("timeformat", DATE_FORMATS)
def test_generate_recovery_token_with_expiration_date(
    authorized_client, client, tokens_file, timeformat, mocker
):
    # Generate token with expiration date
    # Generate expiration date in the future
    expiration_date = datetime.datetime.now() + datetime.timedelta(minutes=5)
    mnemonic_token = rest_make_recovery_token(
        authorized_client, expires_at=expiration_date, timeformat=timeformat
    )

    time_generated = rest_get_recovery_date(authorized_client)
    assert_recovery_recent(time_generated)

    assert rest_get_recovery_status(authorized_client) == {
        "exists": True,
        "valid": True,
        "date": time_generated,
        "expiration": expiration_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "uses_left": None,
    }

    rest_recover_with_mnemonic(client, mnemonic_token, "recover_device")
    # And again
    rest_recover_with_mnemonic(client, mnemonic_token, "recover_device2")

    # Try to use token after expiration date
    mock = mocker.patch(RECOVERY_KEY_VALIDATION_DATETIME, NearFuture)
    device_name = "recovery_device3"
    recovery_response = client.post(
        "/auth/recovery_token/use",
        json={"token": mnemonic_token, "device": device_name},
    )
    assert recovery_response.status_code == 404
    # Assert that the token was not created
    assert device_name not in [
        token["name"] for token in rest_get_tokens_info(authorized_client)
    ]


@pytest.mark.parametrize("timeformat", DATE_FORMATS)
def test_generate_recovery_token_with_expiration_in_the_past(
    authorized_client, tokens_file, timeformat
):
    # Server must return 400 if expiration date is in the past
    expiration_date = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    expiration_date_str = expiration_date.strftime(timeformat)
    response = authorized_client.post(
        "/auth/recovery_token",
        json={"expiration": expiration_date_str},
    )
    assert response.status_code == 400
    assert_no_recovery(authorized_client)


def test_generate_recovery_token_with_invalid_time_format(
    authorized_client, tokens_file
):
    # Server must return 400 if expiration date is in the past
    expiration_date = "invalid_time_format"
    response = authorized_client.post(
        "/auth/recovery_token",
        json={"expiration": expiration_date},
    )
    assert response.status_code == 422
    assert_no_recovery(authorized_client)


def test_generate_recovery_token_with_limited_uses(
    authorized_client, client, tokens_file
):
    # Generate token with limited uses
    mnemonic_token = rest_make_recovery_token(authorized_client, uses=2)

    time_generated = rest_get_recovery_date(authorized_client)
    assert_recovery_recent(time_generated)

    assert rest_get_recovery_status(authorized_client) == {
        "exists": True,
        "valid": True,
        "date": time_generated,
        "expiration": None,
        "uses_left": 2,
    }

    # Try to use the token
    rest_recover_with_mnemonic(client, mnemonic_token, "recover_device")

    assert rest_get_recovery_status(authorized_client) == {
        "exists": True,
        "valid": True,
        "date": time_generated,
        "expiration": None,
        "uses_left": 1,
    }

    # Try to use token again
    rest_recover_with_mnemonic(client, mnemonic_token, "recover_device2")

    assert rest_get_recovery_status(authorized_client) == {
        "exists": True,
        "valid": False,
        "date": time_generated,
        "expiration": None,
        "uses_left": 0,
    }

    # Try to use token after limited uses
    recovery_response = client.post(
        "/auth/recovery_token/use",
        json={"token": mnemonic_token, "device": "recovery_device3"},
    )
    assert recovery_response.status_code == 404


def test_generate_recovery_token_with_negative_uses(
    authorized_client, client, tokens_file
):
    # Generate token with limited uses
    response = authorized_client.post(
        "/auth/recovery_token",
        json={"uses": -2},
    )
    assert response.status_code == 400
    assert_no_recovery(authorized_client)


def test_generate_recovery_token_with_zero_uses(authorized_client, client, tokens_file):
    # Generate token with limited uses
    response = authorized_client.post(
        "/auth/recovery_token",
        json={"uses": 0},
    )
    assert response.status_code == 400
    assert_no_recovery(authorized_client)
