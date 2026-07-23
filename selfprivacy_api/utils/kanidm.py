import asyncio
import gettext
import json
import logging
import os
from json import JSONDecodeError
from typing import Any, Optional

import aiofiles
import httpx
from opentelemetry import trace

from selfprivacy_api.exceptions.users import UserAlreadyExists, UserOrGroupNotFound
from selfprivacy_api.exceptions.users.kanidm_repository import (
    FailedToGetValidKanidmToken,
    KanidmCliSubprocessError,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
)
from selfprivacy_api.utils import get_kanidm_url, temporary_env_var
from selfprivacy_api.utils.redis_pool import RedisPool

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

_ = gettext.gettext

REDIS_TOKEN_KEY = "kanidm:token"

ERROR_CREATING_KANIDM_TOKEN_TEXT = _("Error creating Kanidm token")

_kanidm_client: Optional[httpx.AsyncClient] = None


def kanidm_client() -> httpx.AsyncClient:
    global _kanidm_client
    if _kanidm_client is None:
        _kanidm_client = httpx.AsyncClient(timeout=15)
    return _kanidm_client


def validate_kanidm_response_type(
    data_type: str,
    response_data: Any,
    endpoint: str,
    method: str,
) -> None:
    """
    Validates the type and that content of the response data is not empty.

    Args:
        data_type (str): Expected type of response data ('list' or 'dict').
        response_data (Any): Response data to validate.

    Raises:
        KanidmReturnEmptyResponse: If the response data is empty.
        KanidmReturnUnknownResponseType: If the response data is not of the expected type.
    """

    if response_data is None:
        raise KanidmReturnEmptyResponse(endpoint=endpoint, method=method)

    if data_type == "list" and not isinstance(response_data, list):
        raise KanidmReturnUnknownResponseType(
            response_data=response_data,
            endpoint=endpoint,
            method=method,
        )

    elif data_type == "dict" and not isinstance(response_data, dict):
        raise KanidmReturnUnknownResponseType(
            response_data=response_data,
            endpoint=endpoint,
            method=method,
        )


async def send_kanidm_query(
    endpoint: str, method: str = "GET", data=None
) -> dict | list:
    """
    Sends a request to the Kanidm API.

    Args:
        endpoint (str): The API endpoint.
        method (str, optional): The HTTP method (GET, POST, PATCH, DELETE). Defaults to "GET".
        data (Optional[dict], optional): The data to send in the request body. Defaults to None.

    Returns:
        dict | list: The response data.

    Raises:
        KanidmQueryError: If an error occurs during the request.
        UserAlreadyExists: If the user already exists.
        UserNotFound: If the user is not found.
        UserOrGroupNotFound: If the user or group does not exist.

    Raises from KanidmAdminToken:
        KanidmCliSubprocessError: If there is an error with the Kanidm CLI subprocess.
        KanidmDidNotReturnAdminPassword: If Kanidm did not return the admin password.
        FailedToGetValidKanidmToken: If a valid Kanidm token could not be retrieved.
    """

    full_endpoint = f"{get_kanidm_url()}/v1/{endpoint}"

    with tracer.start_as_current_span(f"kanidm.query {method} {endpoint}") as span:
        span.set_attribute("kanidm.endpoint", endpoint)
        span.set_attribute("http.method", method)

        rejected_token = None
        for attempt in (1, 2):
            token = await KanidmAdminToken.get(rejected_token=rejected_token)
            try:
                response = await kanidm_client().request(
                    method,
                    full_endpoint,
                    json=data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                span.set_attribute("http.status_code", response.status_code)
                response_data = response.json()

            except JSONDecodeError as error:
                raise KanidmQueryError(
                    endpoint=endpoint,
                    method=method,
                    description=_("No JSON found in Kanidm response."),
                    error_text=error,
                )
            except httpx.RequestError as error:
                raise KanidmQueryError(
                    endpoint=endpoint,
                    method=method,
                    error_text=error,
                    description=_("Kanidm is not responding to requests."),
                )
            except Exception as error:
                raise KanidmQueryError(
                    endpoint=endpoint,
                    method=method,
                    error_text=error,
                )

            if (
                attempt == 1
                and response.status_code != 200
                and response_data == "notauthenticated"
            ):
                await KanidmAdminToken._delete_kanidm_token_from_db()
                span.add_event("Kanidm token rejected, retrying with a new one")
                rejected_token = token
                continue

            if response.status_code != 200:
                _raise_for_error_response(response, response_data, endpoint, method)

            return response_data

        raise KanidmQueryError(
            endpoint=endpoint,
            method=method,
            error_text="",
            description=_("We somehow got into unreachable code."),
        )


def _raise_for_error_response(
    response: httpx.Response,
    response_data: dict | list | str,
    endpoint: str,
    method: str,
) -> None:
    """Translate a non-200 Kanidm response into the appropriate exception."""
    if isinstance(response_data, dict):
        if "conflicting_attributes" in response_data:
            raise UserAlreadyExists

    if isinstance(response_data, str):
        if response_data == "nomatchingentries":
            raise UserOrGroupNotFound
        if response_data == "accessdenied":
            raise KanidmQueryError(
                endpoint=endpoint,
                method=method,
                error_text=_("Kanidm access issue"),
            )
        if response_data == "notauthenticated":
            raise FailedToGetValidKanidmToken

    raise KanidmQueryError(
        error_text=response.text,
        endpoint=endpoint,
        method=method,
    )


class KanidmAdminToken:
    """
    Manages the administrative token for Kanidm.

    Token sources, in priority order: Redis, the token file provided by the
    NixOS module, and CLI regeneration.

    Methods:
        get(rejected_token=None) -> str:
            Retrieves the current token. When Kanidm has rejected a token,
            skips it and retries with a rotated or newly generated token.

        _create_and_save_token(kanidm_admin_password: str) -> str:
            Creates a new token using the admin password and saves it to Redis.

        reset_idm_admin_password() -> str:
            Resets the Kanidm admin password and returns the new password.

        _delete_kanidm_token_from_db() -> None:
            Deletes the admin token from Redis.

        _is_token_valid() -> bool:
            Sends a request to kanidm to check the validity of the token.
    """

    @staticmethod
    async def get(rejected_token: Optional[str] = None) -> str:
        if rejected_token is None:
            redis = RedisPool().get_connection_async()
            kanidm_admin_token: str | None = await redis.get(REDIS_TOKEN_KEY)
            if kanidm_admin_token:
                return kanidm_admin_token

            logging.warning(
                "No Kanidm admin token in Redis. "
                "Trying to retrieve it from the environment."
            )

        new_kanidm_admin_token = await KanidmAdminToken._get_admin_token_from_env()
        if new_kanidm_admin_token is not None:
            if rejected_token is None:
                return new_kanidm_admin_token
            if new_kanidm_admin_token != rejected_token and (
                await KanidmAdminToken._is_token_valid(new_kanidm_admin_token)
            ):
                return new_kanidm_admin_token

        logging.warning("The Kanidm admin token is missing or invalid. Regenerating.")

        kanidm_admin_password = await KanidmAdminToken.reset_idm_admin_password()
        return await KanidmAdminToken._create_and_save_token(kanidm_admin_password)

    @staticmethod
    async def _get_admin_token_from_env() -> Optional[str]:
        redis = RedisPool().get_connection_async()
        token_path = os.environ.get("KANIDM_ADMIN_TOKEN_FILE")
        if not token_path:
            logger.warning(
                "KANIDM_ADMIN_TOKEN_FILE environment variable is not set. "
                "The Kanidm admin token will be generated."
            )
            return None
        try:
            async with aiofiles.open(token_path, mode="r") as file:
                token = await file.read()
                token = token.strip()
                if not token:
                    logger.warning(
                        "KANIDM_ADMIN_TOKEN_FILE is empty. "
                        "The Kanidm admin token will be generated."
                    )
                    return None
                await redis.set(REDIS_TOKEN_KEY, token)
                return token
        except FileNotFoundError:
            logger.warning(
                f"KANIDM_ADMIN_TOKEN_FILE '{token_path}' not found. "
                "The Kanidm admin token will be generated."
            )
            return None
        except Exception as error:
            logger.warning(
                f"Error reading KANIDM_ADMIN_TOKEN_FILE '{token_path}': {error}. "
                "The Kanidm admin token will be generated."
            )
            return None

    @staticmethod
    async def _create_and_save_token(kanidm_admin_password: str) -> str:
        redis = RedisPool().get_connection_async()

        with temporary_env_var(key="KANIDM_PASSWORD", value=kanidm_admin_password):
            command = ["kanidm", "login", "-D", "idm_admin"]

            try:
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise KanidmCliSubprocessError(
                        command=" ".join(command),
                        error=stderr.decode(errors="replace"),
                    )

                command = [
                    "kanidm",
                    "service-account",
                    "api-token",
                    "generate",
                    "sp.selfprivacy-api.service-account",
                    "kanidm_service_account_token",
                    "--readwrite",
                ]

                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise KanidmCliSubprocessError(
                        command=" ".join(command),
                        error=stderr.decode(errors="replace"),
                    )

            except OSError as error:
                raise KanidmCliSubprocessError(
                    command=" ".join(command),
                    error=str(error),
                )

        kanidm_admin_token = stdout.decode(errors="replace").splitlines()[-1]

        await redis.set(REDIS_TOKEN_KEY, kanidm_admin_token)
        return kanidm_admin_token

    @staticmethod
    async def reset_idm_admin_password() -> str:
        command = [
            "kanidmd",
            "scripting",
            "recover-account",
            "idm_admin",
            "-c",
            "/etc/kanidm/server.toml",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise KanidmCliSubprocessError(
                    command=" ".join(command),
                    error=stderr.decode(errors="replace"),
                )
        except OSError as error:
            raise KanidmCliSubprocessError(
                command=" ".join(command),
                error=str(error),
            )

        output = stdout.decode(errors="replace")

        try:
            response = json.loads(output)
        except json.JSONDecodeError as error:
            raise KanidmDidNotReturnAdminPassword(
                command=" ".join(command),
                output=output,
            ) from error

        new_kanidm_admin_password = response.get("output")
        if (
            not isinstance(new_kanidm_admin_password, str)
            or not new_kanidm_admin_password
        ):
            raise KanidmDidNotReturnAdminPassword(
                command=" ".join(command),
                output=output,
            )

        return new_kanidm_admin_password

    @staticmethod
    async def _is_token_valid(token: str) -> bool:
        try:
            response = await kanidm_client().get(
                f"{get_kanidm_url()}/v1/person/root",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    @staticmethod
    async def _delete_kanidm_token_from_db() -> None:
        redis = RedisPool().get_connection_async()
        await redis.delete(REDIS_TOKEN_KEY)
