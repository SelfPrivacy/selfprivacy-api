# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import asyncio
import json
import os
from types import SimpleNamespace
from unittest.mock import call as mocker_call

import httpx
import pytest

from selfprivacy_api.exceptions.kanidm import (
    FailedToGetValidKanidmToken,
    KanidmCliSubprocessError,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
)
from selfprivacy_api.exceptions.users import UserAlreadyExists, UserOrGroupNotFound
from selfprivacy_api.utils.kanidm import (
    REDIS_TOKEN_KEY,
    KanidmAdminToken,
    kanidm_client,
    send_kanidm_query,
    validate_kanidm_response_type,
)
from selfprivacy_api.utils.redis_pool import RedisPool

LOGIN_COMMAND = ["kanidm", "login", "-D", "idm_admin"]
GENERATE_COMMAND = [
    "kanidm",
    "service-account",
    "api-token",
    "generate",
    "--readwrite",
    "sp.selfprivacy-api.service-account",
    "kanidm_service_account_token",
]
RECOVER_COMMAND = [
    "kanidmd",
    "scripting",
    "recover-account",
    "idm_admin",
    "-c",
    "/etc/kanidm/server.toml",
]


@pytest.fixture
async def redis():
    connection = RedisPool().get_connection_async()
    await connection.delete(REDIS_TOKEN_KEY)
    yield connection
    await connection.delete(REDIS_TOKEN_KEY)
    await connection.aclose()


class FakeProcess:
    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr


@pytest.fixture
def fake_kanidm_cli(mocker):
    """
    Patches asyncio.create_subprocess_exec at the module lookup site.
    Feed it FakeProcess objects or exceptions via `.processes`; it records
    exact argv in `.calls` and the KANIDM_PASSWORD env value at call time in
    `.env_passwords`.
    """
    state = SimpleNamespace(processes=[], calls=[], env_passwords=[])

    async def fake_exec(*args, **kwargs):
        state.calls.append((args, kwargs))
        state.env_passwords.append(os.environ.get("KANIDM_PASSWORD"))
        result = state.processes.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    mocker.patch(
        "selfprivacy_api.utils.kanidm.asyncio.create_subprocess_exec",
        new=fake_exec,
    )
    return state


# --- Response validation ------------------------------------------------------


def test_validate_kanidm_response_type_raises_for_none():
    with pytest.raises(KanidmReturnEmptyResponse):
        validate_kanidm_response_type(
            data_type="dict",
            response_data=None,
            endpoint="person/root",
            method="GET",
        )


@pytest.mark.parametrize(
    "data_type,response_data",
    [
        ("list", {}),
        ("dict", []),
        ("dict", "some string"),
    ],
)
def test_validate_kanidm_response_type_raises_for_unexpected_type(
    data_type, response_data
):
    with pytest.raises(KanidmReturnUnknownResponseType):
        validate_kanidm_response_type(
            data_type=data_type,
            response_data=response_data,
            endpoint="person/root",
            method="GET",
        )


@pytest.mark.parametrize(
    "data_type,response_data",
    [
        ("list", []),
        ("dict", {"a": 1}),
    ],
)
def test_validate_kanidm_response_type_accepts_expected_types(data_type, response_data):
    validate_kanidm_response_type(
        data_type=data_type,
        response_data=response_data,
        endpoint="person/root",
        method="GET",
    )


# --- send_kanidm_query --------------------------------------------------------


async def test_send_kanidm_query_success_sends_expected_request(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, {"ok": True})

    result = await send_kanidm_query("person/root", method="PATCH", data={"a": 1})

    assert result == {"ok": True}
    assert len(kanidm_api.requests) == 1
    request = kanidm_api.requests[0]
    assert request.method == "PATCH"
    assert str(request.url) == "https://auth.test.tld/v1/person/root"
    assert json.loads(request.content) == {"a": 1}
    assert request.headers["authorization"] == "Bearer token-123"
    assert request.headers["content-type"] == "application/json"
    assert request.extensions["timeout"]["read"] == 15


async def test_send_kanidm_query_reuses_one_http_client(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, {"ok": 1})
    kanidm_api.respond(200, {"ok": 2})

    await send_kanidm_query("person/root")
    await send_kanidm_query("person/root")

    assert kanidm_client() is kanidm_client()
    assert len(kanidm_api.requests) == 2


async def test_send_kanidm_query_non_json_response_raises_query_error(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond_raw(httpx.Response(200, content=b"not json"))

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root")

    assert error.value.endpoint == "https://auth.test.tld/v1/person/root"
    assert error.value.method == "GET"
    assert "No JSON found in Kanidm response." in str(error.value.description)
    assert (
        "Endpoint: https://auth.test.tld/v1/person/root"
        in error.value.get_error_message()
    )


async def test_send_kanidm_query_connect_error_raises_query_error(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.fail(httpx.ConnectError("connection failed"))

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root", method="POST")

    assert error.value.endpoint == "https://auth.test.tld/v1/person/root"
    assert error.value.method == "POST"
    assert "Kanidm is not responding to requests." in str(error.value.description)
    # transport errors are not retried
    assert len(kanidm_api.requests) == 1


async def test_send_kanidm_query_timeout_raises_query_error(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.fail(httpx.TimeoutException("timed out"))

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root")

    assert "Kanidm is not responding to requests." in str(error.value.description)


async def test_send_kanidm_query_duplicate_raises_user_already_exists(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    # Real response of a live Kanidm server (captured 2026-07-07):
    body = {
        "conflicting_attributes": ["mail", "name", "spn"],
        "error": "Attribute uniqueness error",
    }
    kanidm_api.respond(409, body)

    with pytest.raises(UserAlreadyExists):
        await send_kanidm_query("person", method="POST", data={})


async def test_send_kanidm_query_nomatchingentries_raises_user_or_group_not_found(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(404, "nomatchingentries")

    with pytest.raises(UserOrGroupNotFound):
        await send_kanidm_query("person/ghost")


async def test_send_kanidm_query_accessdenied_raises_query_error(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(403, "accessdenied")

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root")

    assert error.value.endpoint == "https://auth.test.tld/v1/person/root"
    assert "Kanidm access issue" in error.value.description
    assert error.value.error_text == "accessdenied"


async def test_send_kanidm_query_notauthenticated_retries_once_then_succeeds(
    redis, kanidm_api, mock_kanidm_domain, mock_admin_token
):
    await redis.set(REDIS_TOKEN_KEY, "newer-token")
    mock_admin_token.side_effect = ["token-123", "newer-token"]
    kanidm_api.respond(401, "notauthenticated")
    kanidm_api.respond(200, {"ok": True})

    result = await send_kanidm_query("person/root")

    assert result == {"ok": True}
    assert len(kanidm_api.requests) == 2
    # A late rejection of the old token must not delete a newer cached token.
    assert await redis.get(REDIS_TOKEN_KEY) == "newer-token"
    # attempt 1 uses the cached chain, attempt 2 knows what was rejected
    assert mock_admin_token.await_args_list == [
        mocker_call(rejected_token=None),
        mocker_call(rejected_token="token-123"),
    ]


async def test_send_kanidm_query_notauthenticated_twice_raises_token_error(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(401, "notauthenticated")
    kanidm_api.respond(401, "notauthenticated")

    with pytest.raises(FailedToGetValidKanidmToken):
        await send_kanidm_query("person/root")

    # no third attempt
    assert len(kanidm_api.requests) == 2


async def test_send_kanidm_query_generic_error_includes_response_text(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(500, {"error": "boom"})

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root")

    assert error.value.error_text == '{"error": "boom"}'
    assert error.value.endpoint == "https://auth.test.tld/v1/person/root"


# --- KanidmAdminToken.get() -----------------------------------------------------


async def test_get_returns_redis_token_without_validation(
    redis, kanidm_api, mock_kanidm_domain
):
    # Tokens are used optimistically; a rejected token is handled by
    # send_kanidm_query's retry, not by pre-validation here.
    await redis.set(REDIS_TOKEN_KEY, "redis-token")

    token = await KanidmAdminToken.get()

    assert token == "redis-token"
    assert kanidm_api.requests == []


async def test_get_without_redis_token_reads_env_file(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("  env-token  \n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))

    token = await KanidmAdminToken.get()

    assert token == "env-token"  # stripped
    assert await redis.get(REDIS_TOKEN_KEY) == "env-token"
    assert kanidm_api.requests == []


# `rejected_token` is passed by send_kanidm_query's retry after Kanidm refuses the
# cached token. That exact token is ignored; a newer cached token is reused.
# An env token is adopted only if it differs from the rejected one and passes
# a probe request.


async def test_get_rejected_token_adopts_rotated_env_token(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path, fake_kanidm_cli
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("rotated-env-token\n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))
    kanidm_api.respond(200, {"user": "root"})  # the probe

    token = await KanidmAdminToken.get(rejected_token="rejected-token")

    assert token == "rotated-env-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "rotated-env-token"
    assert len(kanidm_api.requests) == 1
    probe = kanidm_api.requests[0]
    assert probe.method == "GET"
    assert str(probe.url) == "https://auth.test.tld/v1/person/root"
    assert probe.headers["authorization"] == "Bearer rotated-env-token"
    # no idm_admin password reset, no token minted
    assert fake_kanidm_cli.calls == []


async def test_get_rejected_token_reuses_newer_cached_token(
    redis, monkeypatch, fake_kanidm_cli
):
    await redis.set(REDIS_TOKEN_KEY, "newer-token")
    monkeypatch.delenv("KANIDM_ADMIN_TOKEN_FILE", raising=False)

    token = await KanidmAdminToken.get(rejected_token="rejected-token")

    assert token == "newer-token"
    assert fake_kanidm_cli.calls == []


async def test_get_rejected_token_matching_env_regenerates_without_probe(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path, fake_kanidm_cli
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("rejected-token\n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(stdout=b'{"output": "recovered-password"}'),
            FakeProcess(),
            FakeProcess(stdout=b"generated-token\n"),
        ]
    )

    token = await KanidmAdminToken.get(rejected_token="rejected-token")

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"
    # probing the very token that was just rejected would be pointless
    assert kanidm_api.requests == []
    assert fake_kanidm_cli.calls[0][0] == tuple(RECOVER_COMMAND)


async def test_get_rejected_token_with_unusable_env_token_regenerates(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path, fake_kanidm_cli
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("stale-env-token\n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))
    kanidm_api.respond(401, "notauthenticated")  # the probe fails
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(stdout=b'{"output": "recovered-password"}'),
            FakeProcess(),
            FakeProcess(stdout=b"generated-token\n"),
        ]
    )

    token = await KanidmAdminToken.get(rejected_token="rejected-token")

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"
    assert len(kanidm_api.requests) == 1  # exactly one probe, then regen


async def test_get_rejected_token_without_env_regenerates(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, fake_kanidm_cli
):
    await redis.set(REDIS_TOKEN_KEY, "rejected-token")
    monkeypatch.delenv("KANIDM_ADMIN_TOKEN_FILE", raising=False)
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(stdout=b'{"output": "recovered-password"}'),
            FakeProcess(),
            FakeProcess(stdout=b"generated-token\n"),
        ]
    )

    token = await KanidmAdminToken.get(rejected_token="rejected-token")

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"
    assert kanidm_api.requests == []


async def test_get_concurrent_rejected_token_regeneration_runs_cli_once(
    redis, monkeypatch, fake_kanidm_cli
):
    await redis.set(REDIS_TOKEN_KEY, "rejected-token")
    monkeypatch.delenv("KANIDM_ADMIN_TOKEN_FILE", raising=False)
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(stdout=b'{"output": "recovered-password"}'),
            FakeProcess(),
            FakeProcess(stdout=b"generated-token\n"),
        ]
    )

    first_get = asyncio.create_task(
        KanidmAdminToken.get(rejected_token="rejected-token")
    )
    second_get = asyncio.create_task(
        KanidmAdminToken.get(rejected_token="rejected-token")
    )
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    tokens = await asyncio.wait_for(asyncio.gather(first_get, second_get), timeout=5)

    assert tokens == ["generated-token", "generated-token"]
    assert [call[0] for call in fake_kanidm_cli.calls] == [
        tuple(RECOVER_COMMAND),
        tuple(LOGIN_COMMAND),
        tuple(GENERATE_COMMAND),
    ]


async def test_get_regenerates_token_when_no_sources(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, fake_kanidm_cli
):
    monkeypatch.delenv("KANIDM_ADMIN_TOKEN_FILE", raising=False)
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(stdout=b'{"output": "recovered-password"}'),  # recover
            FakeProcess(),  # login
            FakeProcess(stdout=b"info line\ngenerated-token\n"),  # generate
        ]
    )

    token = await KanidmAdminToken.get()

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"
    # the freshly generated token is returned without any HTTP validation
    assert kanidm_api.requests == []
    assert [call[0] for call in fake_kanidm_cli.calls] == [
        tuple(RECOVER_COMMAND),
        tuple(LOGIN_COMMAND),
        tuple(GENERATE_COMMAND),
    ]
    assert fake_kanidm_cli.env_passwords == [
        None,
        "recovered-password",
        "recovered-password",
    ]


async def test_get_regenerates_token_when_env_file_missing(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path, fake_kanidm_cli
):
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(tmp_path / "missing.token"))
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(stdout=b'{"output": "recovered-password"}'),
            FakeProcess(),
            FakeProcess(stdout=b"generated-token\n"),
        ]
    )

    token = await KanidmAdminToken.get()

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"


async def test_get_regenerates_token_when_env_file_empty(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path, fake_kanidm_cli
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text(" \n\t ")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(stdout=b'{"output": "recovered-password"}'),
            FakeProcess(),
            FakeProcess(stdout=b"generated-token\n"),
        ]
    )

    token = await KanidmAdminToken.get()

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"


# --- _get_admin_token_from_env --------------------------------------------------


async def test_get_admin_token_from_env_reads_and_strips(redis, monkeypatch, tmp_path):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("  test-token  \n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))

    token = await KanidmAdminToken._get_admin_token_from_env()

    assert token == "test-token"
    assert await redis.get(REDIS_TOKEN_KEY) is None


async def test_get_admin_token_from_env_returns_none_without_env_var(
    redis, monkeypatch
):
    monkeypatch.delenv("KANIDM_ADMIN_TOKEN_FILE", raising=False)

    token = await KanidmAdminToken._get_admin_token_from_env()

    assert token is None
    assert await redis.get(REDIS_TOKEN_KEY) is None


# --- _create_and_save_token -----------------------------------------------------


async def test_create_and_save_token_success(redis, fake_kanidm_cli):
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(),  # login
            FakeProcess(stdout=b"some line\ngenerated-token\n"),  # generate
        ]
    )

    token = await KanidmAdminToken._create_and_save_token("secret-password")

    # the token is the last line of the generate command's stdout
    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"

    login_args, login_kwargs = fake_kanidm_cli.calls[0]
    assert login_args == tuple(LOGIN_COMMAND)
    assert login_kwargs == {
        "stdout": asyncio.subprocess.PIPE,
        "stderr": asyncio.subprocess.PIPE,
    }

    generate_args, _ = fake_kanidm_cli.calls[1]
    assert generate_args == tuple(GENERATE_COMMAND)

    # KANIDM_PASSWORD is exported only for the duration of the CLI calls
    assert fake_kanidm_cli.env_passwords == ["secret-password", "secret-password"]
    assert "KANIDM_PASSWORD" not in os.environ


async def test_create_and_save_token_login_failure_raises(redis, fake_kanidm_cli):
    fake_kanidm_cli.processes.append(FakeProcess(stderr=b"login failed", returncode=1))

    with pytest.raises(KanidmCliSubprocessError) as error:
        await KanidmAdminToken._create_and_save_token("secret-password")

    assert error.value.command == "kanidm login -D idm_admin"
    assert "login failed" in error.value.error
    assert len(fake_kanidm_cli.calls) == 1  # generate was never attempted
    assert await redis.get(REDIS_TOKEN_KEY) is None


async def test_create_and_save_token_generate_failure_raises(redis, fake_kanidm_cli):
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(),  # login succeeds
            FakeProcess(stderr=b"generate failed", returncode=1),
        ]
    )

    with pytest.raises(KanidmCliSubprocessError) as error:
        await KanidmAdminToken._create_and_save_token("secret-password")

    assert error.value.command == " ".join(GENERATE_COMMAND)
    assert "generate failed" in error.value.error
    assert await redis.get(REDIS_TOKEN_KEY) is None


# --- _reset_idm_admin_password --------------------------------------------------


async def test_reset_password_returns_parsed_password(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(FakeProcess(stdout=b'{"output": "new-password"}'))

    password = await KanidmAdminToken._reset_idm_admin_password()

    assert password == "new-password"
    assert fake_kanidm_cli.calls[0][0] == tuple(RECOVER_COMMAND)


async def test_reset_password_cli_failure_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(
        FakeProcess(stderr=b"recovery failed", returncode=1)
    )

    with pytest.raises(KanidmCliSubprocessError) as error:
        await KanidmAdminToken._reset_idm_admin_password()

    assert error.value.command == " ".join(RECOVER_COMMAND)
    assert "recovery failed" in error.value.error
    assert fake_kanidm_cli.calls[0][0] == tuple(RECOVER_COMMAND)


async def test_reset_password_os_error_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(OSError("recover command missing"))

    with pytest.raises(KanidmCliSubprocessError) as error:
        await KanidmAdminToken._reset_idm_admin_password()

    assert error.value.command == " ".join(RECOVER_COMMAND)
    assert "recover command missing" in error.value.error
    assert fake_kanidm_cli.calls[0][0] == tuple(RECOVER_COMMAND)


async def test_reset_password_non_json_output_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(FakeProcess(stdout=b"no json in this output"))

    with pytest.raises(KanidmDidNotReturnAdminPassword) as error:
        await KanidmAdminToken._reset_idm_admin_password()

    assert error.value.command == " ".join(RECOVER_COMMAND)
    assert "no json in this output" in error.value.output


async def test_reset_password_missing_output_field_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(
        FakeProcess(stdout=b'{"password": "new-password"}')
    )

    with pytest.raises(KanidmDidNotReturnAdminPassword):
        await KanidmAdminToken._reset_idm_admin_password()


async def test_reset_password_empty_output_field_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(FakeProcess(stdout=b'{"output": ""}'))

    with pytest.raises(KanidmDidNotReturnAdminPassword):
        await KanidmAdminToken._reset_idm_admin_password()


# --- _is_token_valid ------------------------------------------------------------


async def test_is_token_valid_true_on_200(kanidm_api, mock_kanidm_domain):
    kanidm_api.respond(200, {"user": "root"})

    assert await KanidmAdminToken._is_token_valid("probe-token") is True

    assert len(kanidm_api.requests) == 1
    probe = kanidm_api.requests[0]
    assert probe.method == "GET"
    assert str(probe.url) == "https://auth.test.tld/v1/person/root"
    assert probe.headers["authorization"] == "Bearer probe-token"


async def test_is_token_valid_false_on_non_200(kanidm_api, mock_kanidm_domain):
    kanidm_api.respond(401, "notauthenticated")

    assert await KanidmAdminToken._is_token_valid("probe-token") is False


async def test_is_token_valid_false_on_http_error(kanidm_api, mock_kanidm_domain):
    kanidm_api.fail(httpx.ConnectError("connection failed"))

    assert await KanidmAdminToken._is_token_valid("probe-token") is False
