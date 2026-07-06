# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import asyncio
import os
from types import SimpleNamespace

import httpx
import pytest

from selfprivacy_api.exceptions.users.kanidm_repository import (
    KanidmCliSubprocessError,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
)
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    REDIS_TOKEN_KEY,
    KanidmAdminToken,
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
    Feed it FakeProcess objects via `.processes`; it records exact argv in
    `.calls` and the KANIDM_PASSWORD env value at call time in
    `.env_passwords`.
    """
    state = SimpleNamespace(processes=[], calls=[], env_passwords=[])

    async def fake_exec(*args, **kwargs):
        state.calls.append((args, kwargs))
        state.env_passwords.append(os.environ.get("KANIDM_PASSWORD"))
        return state.processes.pop(0)

    mocker.patch(
        "selfprivacy_api.repositories.users.kanidm_user_repository."
        "asyncio.create_subprocess_exec",
        new=fake_exec,
    )
    return state


# --- KanidmAdminToken.get() -----------------------------------------------------


async def test_get_returns_redis_token_after_prevalidation(
    redis, kanidm_api, mock_kanidm_domain
):
    await redis.set(REDIS_TOKEN_KEY, "redis-token")
    kanidm_api.respond(200, {"user": "root"})

    token = await KanidmAdminToken.get()

    assert token == "redis-token"
    assert len(kanidm_api.requests) == 1
    request = kanidm_api.requests[0]
    assert request.method == "GET"
    assert str(request.url) == "https://auth.test.tld/v1/person/root"
    assert request.headers["authorization"] == "Bearer redis-token"


async def test_get_with_invalid_redis_token_falls_back_to_env(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path
):
    await redis.set(REDIS_TOKEN_KEY, "stale-token")
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("env-token\n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))

    kanidm_api.respond(401, "notauthenticated")  # stale redis token check
    kanidm_api.respond(200, {"user": "root"})  # env token check

    token = await KanidmAdminToken.get()

    assert token == "env-token"
    assert [request.headers["authorization"] for request in kanidm_api.requests] == [
        "Bearer stale-token",
        "Bearer env-token",
    ]
    assert await redis.get(REDIS_TOKEN_KEY) == "env-token"


async def test_get_without_redis_token_reads_env_file(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("  env-token  \n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))
    kanidm_api.respond(200, {"user": "root"})

    token = await KanidmAdminToken.get()

    assert token == "env-token"  # stripped
    assert await redis.get(REDIS_TOKEN_KEY) == "env-token"
    assert len(kanidm_api.requests) == 1
    assert kanidm_api.requests[0].headers["authorization"] == "Bearer env-token"


async def test_get_regenerates_token_when_no_sources(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, fp, fake_kanidm_cli
):
    monkeypatch.delenv("KANIDM_ADMIN_TOKEN_FILE", raising=False)
    fp.register(RECOVER_COMMAND, stdout='{"output": "recovered-password"}')
    fake_kanidm_cli.processes.extend(
        [
            FakeProcess(),  # login
            FakeProcess(stdout=b"info line\ngenerated-token\n"),  # generate
        ]
    )

    token = await KanidmAdminToken.get()

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"
    # the freshly generated token is returned without any HTTP validation
    assert kanidm_api.requests == []
    assert fp.call_count(RECOVER_COMMAND) == 1
    assert [call[0] for call in fake_kanidm_cli.calls] == [
        tuple(LOGIN_COMMAND),
        tuple(GENERATE_COMMAND),
    ]
    assert fake_kanidm_cli.env_passwords == [
        "recovered-password",
        "recovered-password",
    ]


async def test_get_regenerates_token_when_env_file_missing(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path, fp, fake_kanidm_cli
):
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(tmp_path / "missing.token"))
    fp.register(RECOVER_COMMAND, stdout='{"output": "recovered-password"}')
    fake_kanidm_cli.processes.extend(
        [FakeProcess(), FakeProcess(stdout=b"generated-token\n")]
    )

    token = await KanidmAdminToken.get()

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"


async def test_get_regenerates_token_when_env_file_empty(
    redis, kanidm_api, mock_kanidm_domain, monkeypatch, tmp_path, fp, fake_kanidm_cli
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text(" \n\t ")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))
    fp.register(RECOVER_COMMAND, stdout='{"output": "recovered-password"}')
    fake_kanidm_cli.processes.extend(
        [FakeProcess(), FakeProcess(stdout=b"generated-token\n")]
    )

    token = await KanidmAdminToken.get()

    assert token == "generated-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "generated-token"


# --- _get_admin_token_from_env --------------------------------------------------


async def test_get_admin_token_from_env_reads_strips_and_caches(
    redis, monkeypatch, tmp_path
):
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("  test-token  \n")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))

    token = await KanidmAdminToken._get_admin_token_from_env()

    assert token == "test-token"
    assert await redis.get(REDIS_TOKEN_KEY) == "test-token"


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


# --- _reset_and_save_idm_admin_password -----------------------------------------


def test_reset_password_returns_parsed_password(fp):
    fp.register(RECOVER_COMMAND, stdout='{"output": "new-password"}')

    password = KanidmAdminToken._reset_and_save_idm_admin_password()

    assert password == "new-password"
    assert fp.call_count(RECOVER_COMMAND) == 1


def test_reset_password_non_json_output_raises(fp):
    fp.register(RECOVER_COMMAND, stdout="no json in this output")

    with pytest.raises(KanidmDidNotReturnAdminPassword) as error:
        KanidmAdminToken._reset_and_save_idm_admin_password()

    assert error.value.command == " ".join(RECOVER_COMMAND)
    assert "no json in this output" in error.value.output


def test_reset_password_missing_output_field_raises(fp):
    fp.register(RECOVER_COMMAND, stdout='{"password": "new-password"}')

    with pytest.raises(KanidmDidNotReturnAdminPassword):
        KanidmAdminToken._reset_and_save_idm_admin_password()


def test_reset_password_empty_output_field_raises(fp):
    fp.register(RECOVER_COMMAND, stdout='{"output": ""}')

    with pytest.raises(KanidmDidNotReturnAdminPassword):
        KanidmAdminToken._reset_and_save_idm_admin_password()


# --- _is_token_valid ------------------------------------------------------------


async def test_is_token_valid_returns_true_for_200(kanidm_api, mock_kanidm_domain):
    kanidm_api.respond(200, {"user": "root"})

    result = await KanidmAdminToken._is_token_valid("valid-token")

    assert result is True
    assert len(kanidm_api.requests) == 1
    request = kanidm_api.requests[0]
    assert request.method == "GET"
    assert str(request.url) == "https://auth.test.tld/v1/person/root"
    assert request.headers["authorization"] == "Bearer valid-token"
    assert request.extensions["timeout"]["read"] == 1


async def test_is_token_valid_returns_false_for_notauthenticated(
    kanidm_api, mock_kanidm_domain
):
    kanidm_api.respond(401, "notauthenticated")

    result = await KanidmAdminToken._is_token_valid("invalid-token")

    assert result is False


async def test_is_token_valid_raises_query_error_on_connection_issue(
    kanidm_api, mock_kanidm_domain
):
    kanidm_api.fail(httpx.ConnectError("connection failed"))

    with pytest.raises(KanidmQueryError) as error:
        await KanidmAdminToken._is_token_valid("any-token")

    assert "Connection error" in str(error.value.description)


async def test_is_token_valid_returns_true_for_other_non_200_responses(
    kanidm_api, mock_kanidm_domain
):
    kanidm_api.respond(500, {"error": "boom"})

    result = await KanidmAdminToken._is_token_valid("any-token")

    assert result is True


# --- _delete_kanidm_token_from_db -----------------------------------------------


async def test_delete_kanidm_token_from_db(redis):
    await redis.set(REDIS_TOKEN_KEY, "some-token")

    await KanidmAdminToken._delete_kanidm_token_from_db()

    assert await redis.get(REDIS_TOKEN_KEY) is None
