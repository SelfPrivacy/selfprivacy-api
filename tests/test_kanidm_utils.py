# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

from json import JSONDecodeError
from types import SimpleNamespace

import httpx
import pytest

from selfprivacy_api.exceptions.users import UserAlreadyExists, UserOrGroupNotFound
from selfprivacy_api.exceptions.users.kanidm_repository import (
    FailedToGetValidKanidmToken,
    KanidmCliSubprocessError,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
)
from selfprivacy_api.utils.kanidm import (
    REDIS_TOKEN_KEY,
    KanidmAdminToken,
    check_kanidm_response_type,
    send_kanidm_query,
)


class DummyRedis:
    def __init__(self, initial: dict | None = None):
        self.storage = initial or {}
        self.set_calls = []
        self.delete_calls = []

    async def get(self, key: str):
        return self.storage.get(key)

    async def set(self, key: str, value: str):
        self.storage[key] = value
        self.set_calls.append((key, value))

    async def delete(self, key: str):
        self.storage.pop(key, None)
        self.delete_calls.append(key)


class DummyResponse:
    def __init__(self, status_code: int, json_data, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


class DummyAsyncClient:
    def __init__(
        self,
        *,
        request_response: DummyResponse | None = None,
        request_error: Exception | None = None,
        get_response: DummyResponse | None = None,
        get_error: Exception | None = None,
    ):
        self.request_response = request_response
        self.request_error = request_error
        self.get_response = get_response
        self.get_error = get_error
        self.request_calls = []
        self.get_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, endpoint, **kwargs):
        self.request_calls.append((method, endpoint, kwargs))
        if self.request_error is not None:
            raise self.request_error
        return self.request_response

    async def get(self, endpoint, **kwargs):
        self.get_calls.append((endpoint, kwargs))
        if self.get_error is not None:
            raise self.get_error
        return self.get_response


class DummyProcess:
    def __init__(self, stdout: bytes, stderr: bytes, returncode: int):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr


def patch_redis_pool(mocker, redis: DummyRedis):
    mocker.patch(
        "selfprivacy_api.utils.kanidm.RedisPool",
        return_value=SimpleNamespace(get_connection_async=lambda: redis),
    )


def patch_async_client(mocker, client: DummyAsyncClient):
    mocker.patch(
        "selfprivacy_api.utils.kanidm.httpx.AsyncClient",
        return_value=client,
    )


@pytest.fixture
def get_domain_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.kanidm.get_domain",
        return_value="example.org",
    )
    return mock


@pytest.fixture
def kanidm_admin_token_get_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken.get",
        new=mocker.AsyncMock(return_value="token-123"),
    )
    return mock


def test_check_kanidm_response_type_raises_for_none():
    with pytest.raises(KanidmReturnEmptyResponse):
        check_kanidm_response_type("dict", None, "person/root", "GET")


@pytest.mark.parametrize(
    "data_type,response_data",
    [
        ("list", {}),
        ("dict", []),
    ],
)
def test_check_kanidm_response_type_raises_for_unexpected_type(
    data_type, response_data
):
    with pytest.raises(KanidmReturnUnknownResponseType):
        check_kanidm_response_type(data_type, response_data, "person/root", "GET")


@pytest.mark.asyncio
async def test_send_kanidm_query_success(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_response=DummyResponse(status_code=200, json_data={"ok": True})
    )
    patch_async_client(mocker, client)

    result = await send_kanidm_query("person/root", method="PATCH", data={"a": 1})

    assert result == {"ok": True}
    assert len(client.request_calls) == 1
    method, endpoint, kwargs = client.request_calls[0]
    assert method == "PATCH"
    assert endpoint == "https://auth.example.org/v1/person/root"
    assert kwargs["json"] == {"a": 1}
    assert kwargs["headers"]["Authorization"] == "Bearer token-123"
    assert kwargs["timeout"] == 1


@pytest.mark.asyncio
async def test_send_kanidm_query_json_decode_error(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_response=DummyResponse(
            status_code=200,
            json_data=JSONDecodeError("broken json", "doc", 0),
        )
    )
    patch_async_client(mocker, client)

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root")

    assert error.value.endpoint == "https://auth.example.org/v1/person/root"
    assert error.value.method == "GET"
    assert "No JSON found in Kanidm response" in str(error.value.description)


@pytest.mark.asyncio
async def test_send_kanidm_query_request_error(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_error=httpx.ConnectError(
            "connection failed", request=httpx.Request("GET", "https://test")
        )
    )
    patch_async_client(mocker, client)

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root", method="POST")

    assert error.value.endpoint == "person/root"
    assert error.value.method == "POST"
    assert "Kanidm is not responding to requests." in str(error.value.description)


@pytest.mark.asyncio
async def test_send_kanidm_query_raises_user_already_exists(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_response=DummyResponse(
            status_code=409,
            json_data={"plugin": {"attrunique": "duplicate value detected"}},
        )
    )
    patch_async_client(mocker, client)

    with pytest.raises(UserAlreadyExists):
        await send_kanidm_query("person/root")


@pytest.mark.asyncio
async def test_send_kanidm_query_raises_user_or_group_not_found(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_response=DummyResponse(status_code=404, json_data="nomatchingentries")
    )
    patch_async_client(mocker, client)

    with pytest.raises(UserOrGroupNotFound):
        await send_kanidm_query("person/root")


@pytest.mark.asyncio
async def test_send_kanidm_query_raises_access_denied_error(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_response=DummyResponse(status_code=403, json_data="accessdenied")
    )
    patch_async_client(mocker, client)

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root")

    assert "Kanidm access issue" in error.value.error_text


@pytest.mark.asyncio
async def test_send_kanidm_query_raises_failed_to_get_valid_token(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_response=DummyResponse(status_code=401, json_data="notauthenticated")
    )
    patch_async_client(mocker, client)

    with pytest.raises(FailedToGetValidKanidmToken):
        await send_kanidm_query("person/root")


@pytest.mark.asyncio
async def test_send_kanidm_query_raises_generic_error_for_non_200(
    mocker, get_domain_mock, kanidm_admin_token_get_mock
):
    client = DummyAsyncClient(
        request_response=DummyResponse(
            status_code=500,
            json_data={"error": "boom"},
            text="plain error",
        )
    )
    patch_async_client(mocker, client)

    with pytest.raises(KanidmQueryError) as error:
        await send_kanidm_query("person/root")

    assert "plain error" == error.value.error_text


@pytest.mark.asyncio
async def test_kanidm_admin_token_get_returns_valid_redis_token(mocker):
    redis = DummyRedis(initial={REDIS_TOKEN_KEY: "redis-token"})
    patch_redis_pool(mocker, redis)
    is_token_valid = mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken._is_token_valid",
        new=mocker.AsyncMock(return_value=True),
    )
    get_from_env = mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken._get_admin_token_from_env",
        new=mocker.AsyncMock(),
    )

    token = await KanidmAdminToken.get()

    assert token == "redis-token"
    is_token_valid.assert_awaited_once_with("redis-token")
    get_from_env.assert_not_awaited()


@pytest.mark.asyncio
async def test_kanidm_admin_token_get_falls_back_to_env_token(mocker):
    redis = DummyRedis()
    patch_redis_pool(mocker, redis)
    mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken._is_token_valid",
        new=mocker.AsyncMock(return_value=True),
    )
    mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken._get_admin_token_from_env",
        new=mocker.AsyncMock(return_value="env-token"),
    )
    reset_password = mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken.reset_idm_admin_password"
    )

    token = await KanidmAdminToken.get()

    assert token == "env-token"
    reset_password.assert_not_called()


@pytest.mark.asyncio
async def test_kanidm_admin_token_get_regenerates_token_when_needed(mocker):
    redis = DummyRedis(initial={REDIS_TOKEN_KEY: "old-token"})
    patch_redis_pool(mocker, redis)
    mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken._is_token_valid",
        new=mocker.AsyncMock(return_value=False),
    )
    mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken._get_admin_token_from_env",
        new=mocker.AsyncMock(return_value=None),
    )
    mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken.reset_idm_admin_password",
        return_value="new-password",
    )
    create_and_save = mocker.patch(
        "selfprivacy_api.utils.kanidm.KanidmAdminToken._create_and_save_token",
        new=mocker.AsyncMock(return_value="new-token"),
    )

    token = await KanidmAdminToken.get()

    assert token == "new-token"
    create_and_save.assert_awaited_once_with("new-password")


@pytest.mark.asyncio
async def test_get_admin_token_from_env_missing_env_var(mocker, monkeypatch):
    redis = DummyRedis()
    patch_redis_pool(mocker, redis)
    monkeypatch.delenv("KANIDM_ADMIN_TOKEN_FILE", raising=False)

    token = await KanidmAdminToken._get_admin_token_from_env()

    assert token is None
    assert redis.set_calls == []


@pytest.mark.asyncio
async def test_get_admin_token_from_env_reads_file_and_saves_to_redis(
    mocker, monkeypatch, tmp_path
):
    redis = DummyRedis()
    patch_redis_pool(mocker, redis)
    token_file = tmp_path / "kanidm.token"
    token_file.write_text("  test-token  ")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))

    token = await KanidmAdminToken._get_admin_token_from_env()

    assert token == "test-token"
    assert redis.storage[REDIS_TOKEN_KEY] == "test-token"
    assert redis.set_calls == [(REDIS_TOKEN_KEY, "test-token")]


@pytest.mark.asyncio
async def test_get_admin_token_from_env_empty_file(mocker, monkeypatch, tmp_path):
    redis = DummyRedis()
    patch_redis_pool(mocker, redis)
    token_file = tmp_path / "kanidm.token"
    token_file.write_text(" \n\t ")
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(token_file))

    token = await KanidmAdminToken._get_admin_token_from_env()

    assert token is None
    assert redis.set_calls == []


@pytest.mark.asyncio
async def test_get_admin_token_from_env_missing_file(mocker, monkeypatch, tmp_path):
    redis = DummyRedis()
    patch_redis_pool(mocker, redis)
    missing_file = tmp_path / "missing.token"
    monkeypatch.setenv("KANIDM_ADMIN_TOKEN_FILE", str(missing_file))

    token = await KanidmAdminToken._get_admin_token_from_env()

    assert token is None
    assert redis.set_calls == []


@pytest.mark.asyncio
async def test_create_and_save_token_success(mocker):
    redis = DummyRedis()
    patch_redis_pool(mocker, redis)

    login_proc = DummyProcess(stdout=b"", stderr=b"", returncode=0)
    generate_proc = DummyProcess(
        stdout=b"some line\ngenerated-token\n", stderr=b"", returncode=0
    )
    create_subprocess = mocker.patch(
        "selfprivacy_api.utils.kanidm.asyncio.create_subprocess_exec",
        side_effect=[login_proc, generate_proc],
    )

    token = await KanidmAdminToken._create_and_save_token("secret-password")

    assert token == "generated-token"
    assert redis.storage[REDIS_TOKEN_KEY] == "generated-token"
    assert create_subprocess.call_count == 2
    login_call = create_subprocess.call_args_list[0]
    generate_call = create_subprocess.call_args_list[1]
    assert list(login_call[0][:4]) == ["kanidm", "login", "-D", "idm_admin"]
    assert list(generate_call[0][:4]) == [
        "kanidm",
        "service-account",
        "api-token",
        "generate",
    ]


@pytest.mark.asyncio
async def test_create_and_save_token_raises_on_login_error(mocker):
    redis = DummyRedis()
    patch_redis_pool(mocker, redis)
    failing_login_proc = DummyProcess(stdout=b"", stderr=b"login failed", returncode=1)
    mocker.patch(
        "selfprivacy_api.utils.kanidm.asyncio.create_subprocess_exec",
        return_value=failing_login_proc,
    )

    with pytest.raises(KanidmCliSubprocessError) as error:
        await KanidmAdminToken._create_and_save_token("secret-password")

    assert "kanidm login -D idm_admin" == error.value.command
    assert "login failed" in error.value.error


def test_reset_idm_admin_password_returns_parsed_password(mocker):
    mocker.patch(
        "selfprivacy_api.utils.kanidm.subprocess.check_output",
        return_value='noise {"password":"fresh-password"} more-noise',
    )

    password = KanidmAdminToken.reset_idm_admin_password()

    assert password == "fresh-password"


def test_reset_idm_admin_password_raises_when_password_missing(mocker):
    mocker.patch(
        "selfprivacy_api.utils.kanidm.subprocess.check_output",
        return_value="no password in this output",
    )

    with pytest.raises(KanidmDidNotReturnAdminPassword):
        KanidmAdminToken.reset_idm_admin_password()


@pytest.mark.asyncio
async def test_is_token_valid_returns_true_for_200_response(mocker, get_domain_mock):
    client = DummyAsyncClient(
        get_response=DummyResponse(status_code=200, json_data={"user": "root"})
    )
    patch_async_client(mocker, client)

    result = await KanidmAdminToken._is_token_valid("valid-token")

    assert result is True
    assert len(client.get_calls) == 1
    endpoint, kwargs = client.get_calls[0]
    assert endpoint == "https://auth.example.org/v1/person/root"
    assert kwargs["headers"]["Authorization"] == "Bearer valid-token"
    assert kwargs["timeout"] == 1


@pytest.mark.asyncio
async def test_is_token_valid_returns_false_for_notauthenticated(
    mocker, get_domain_mock
):
    client = DummyAsyncClient(
        get_response=DummyResponse(status_code=401, json_data="notauthenticated")
    )
    patch_async_client(mocker, client)

    result = await KanidmAdminToken._is_token_valid("invalid-token")

    assert result is False


@pytest.mark.asyncio
async def test_is_token_valid_raises_query_error_on_connection_issue(
    mocker, get_domain_mock
):
    client = DummyAsyncClient(
        get_error=httpx.ConnectError(
            "connection failed", request=httpx.Request("GET", "https://test")
        )
    )
    patch_async_client(mocker, client)

    with pytest.raises(KanidmQueryError):
        await KanidmAdminToken._is_token_valid("any-token")
