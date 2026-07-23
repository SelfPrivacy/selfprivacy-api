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
)
from selfprivacy_api.utils.kanidm import (
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
    "sp.selfprivacy-api.service-account",
    "kanidm_service_account_token",
    "--readwrite",
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
        "selfprivacy_api.utils.kanidm.asyncio.create_subprocess_exec",
        new=fake_exec,
    )
    return state


# --- KanidmAdminToken.get() -----------------------------------------------------


async def test_get_returns_redis_token_without_validation(
    redis, kanidm_api, mock_kanidm_domain
):
    # Tokens are used optimistically; a rejected token is handled by
    # _send_query's retry, not by pre-validation here.
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


# `rejected_token` is passed by _send_query's retry after Kanidm refuses the
# cached token. The Redis cache is always skipped; the env token is adopted
# only if it differs from the rejected one AND passes a probe request.


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
    await redis.set(REDIS_TOKEN_KEY, "rejected-token")  # skipped entirely
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


# --- reset_idm_admin_password ---------------------------------------------------


async def test_reset_password_returns_parsed_password(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(FakeProcess(stdout=b'{"output": "new-password"}'))

    password = await KanidmAdminToken.reset_idm_admin_password()

    assert password == "new-password"
    assert fake_kanidm_cli.calls[0][0] == tuple(RECOVER_COMMAND)


async def test_reset_password_non_json_output_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(FakeProcess(stdout=b"no json in this output"))

    with pytest.raises(KanidmDidNotReturnAdminPassword) as error:
        await KanidmAdminToken.reset_idm_admin_password()

    assert error.value.command == " ".join(RECOVER_COMMAND)
    assert "no json in this output" in error.value.output


async def test_reset_password_missing_output_field_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(
        FakeProcess(stdout=b'{"password": "new-password"}')
    )

    with pytest.raises(KanidmDidNotReturnAdminPassword):
        await KanidmAdminToken.reset_idm_admin_password()


async def test_reset_password_empty_output_field_raises(fake_kanidm_cli):
    fake_kanidm_cli.processes.append(FakeProcess(stdout=b'{"output": ""}'))

    with pytest.raises(KanidmDidNotReturnAdminPassword):
        await KanidmAdminToken.reset_idm_admin_password()


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


# --- _delete_kanidm_token_from_db -----------------------------------------------


async def test_delete_kanidm_token_from_db(redis):
    await redis.set(REDIS_TOKEN_KEY, "some-token")

    await KanidmAdminToken._delete_kanidm_token_from_db()

    assert await redis.get(REDIS_TOKEN_KEY) is None
