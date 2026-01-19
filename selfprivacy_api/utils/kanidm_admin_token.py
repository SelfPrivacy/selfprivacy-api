import asyncio
import gettext
import logging
import os
import re
import subprocess
from typing import Optional

import httpx

from selfprivacy_api.exceptions.users.kanidm_repository import (
    KanidmCliSubprocessError,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
)
from selfprivacy_api.utils import get_domain, temporary_env_var
from selfprivacy_api.utils.redis_pool import RedisPool

logger = logging.getLogger(__name__)

_ = gettext.gettext

REDIS_TOKEN_KEY = "kanidm:token"

ERROR_CREATING_KANIDM_TOKEN_TEXT = _("Error creating Kanidm token")


def get_kanidm_url():
    return f"https://auth.{get_domain()}"  # TODO better place?


class KanidmAdminToken:
    """
    Manages the administrative token for Kanidm.

    Methods:
        get() -> str:
            Retrieves the current administrative token. If absent, resets the admin password and creates a new token.

        _create_and_save_token(kanidm_admin_password: str) -> str:
            Creates a new token using the admin password and saves it to Redis.

        _reset_and_save_idm_admin_password() -> str:
            Resets the Kanidm admin password and returns the new password.

        _delete_kanidm_token_from_db() -> None:
            Deletes the admin token from Redis.

        _is_token_valid() -> bool:
            Sends a request to kanidm to check the validity of the token.
    """

    @staticmethod
    async def get() -> str:
        redis = RedisPool().get_connection_async()
        kanidm_admin_token: str | None = await redis.get(REDIS_TOKEN_KEY)

        if kanidm_admin_token and await KanidmAdminToken._is_token_valid(
            kanidm_admin_token
        ):
            return kanidm_admin_token

        logging.warning(
            "The Kanidm admin token from Redis is missing or invalid. Trying to retrieve it from the environment."
        )

        new_kanidm_admin_token = await KanidmAdminToken._get_admin_token_from_env()
        if new_kanidm_admin_token and await KanidmAdminToken._is_token_valid(
            new_kanidm_admin_token
        ):
            return new_kanidm_admin_token

        logging.warning(
            "The Kanidm admin token from the environment is missing or invalid. Regenerating."
        )

        kanidm_admin_password = KanidmAdminToken.reset_idm_admin_password()
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
            with open(token_path, "r") as file:
                token = file.read().strip()
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
            command = "kanidm login -D idm_admin"

            try:
                proc = await asyncio.create_subprocess_exec(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise KanidmCliSubprocessError(
                        command=command,
                        description=ERROR_CREATING_KANIDM_TOKEN_TEXT,
                        error=stderr.decode(errors="replace"),
                    )

                command = "kanidm service-account api-token generate --rw sp.selfprivacy-api.service-account kanidm_service_account_token"
                proc = await asyncio.create_subprocess_exec(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise KanidmCliSubprocessError(
                        command=command,
                        description=ERROR_CREATING_KANIDM_TOKEN_TEXT,
                        error=stderr.decode(errors="replace"),
                    )

            except OSError as error:
                raise KanidmCliSubprocessError(
                    command=command,
                    description=ERROR_CREATING_KANIDM_TOKEN_TEXT,
                    error=str(error),
                )

        kanidm_admin_token = stdout.decode(errors="replace").splitlines()[-1]

        await redis.set(REDIS_TOKEN_KEY, kanidm_admin_token)
        return kanidm_admin_token

    @staticmethod
    def reset_idm_admin_password() -> str:
        command = [
            "kanidmd",
            "recover-account",
            "-c",
            "/etc/kanidm/server.toml",
            "idm_admin",
            "-o",
            "json",
        ]

        output = subprocess.check_output(
            command,
            text=True,
        )

        regex_pattern = r'"password":"([^"]+)"'
        match = re.search(regex_pattern, output)
        if match:
            new_kanidm_admin_password = match.group(
                1
            )  # we have many non-JSON strings in output
        else:
            raise KanidmDidNotReturnAdminPassword(
                command=" ".join(command),
                regex_pattern=regex_pattern,
                output=output,
            )

        return new_kanidm_admin_password

    @staticmethod
    async def _is_token_valid(token: str) -> bool:
        endpoint = f"{get_kanidm_url()}/v1/person/root"
        method = "GET"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    timeout=1,
                )

        except (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.RequestError,
        ) as error:
            raise KanidmQueryError(
                description="Kanidm is not responding to requests. Connection error.",
                endpoint=endpoint,
                method=method,
                error_text=error,
            )

        except Exception as error:
            raise KanidmQueryError(
                description="Unknown error while checking the Kanidm admin token.",
                endpoint=endpoint,
                method=method,
                error_text=error,
            )

        response_data = response.json()

        # we do not handle the other errors, this is handled by the main function in KanidmUserRepository._send_query
        if response.status_code != 200:
            if isinstance(response_data, str) and response_data == "notauthenticated":
                logger.error("Kanidm token is not valid")
                return False
        return True

    @staticmethod
    async def _delete_kanidm_token_from_db() -> None:
        redis = RedisPool().get_connection_async()
        await redis.delete(REDIS_TOKEN_KEY)
