import asyncio
import gettext
import logging
import re
from textwrap import dedent

from selfprivacy_api.exceptions.kanidm import (
    KANIDM_DESCRIPTION,
    KANIDM_PROBLEMS,
    STANDARD_OUTPUT_EXAMPLE,
    FailedToSetupKanidmMinimumCredentialType,
)
from selfprivacy_api.exceptions.system import FailedToFindResult
from selfprivacy_api.exceptions.users.kanidm_repository import KanidmCliSubprocessError
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType
from selfprivacy_api.utils import temporary_env_var
from selfprivacy_api.utils.kanidm_admin_token import KanidmAdminToken

logger = logging.getLogger(__name__)

_ = gettext.gettext


KANIDM_GET_MIN_CREDENTIAL_TYPE_ERROR_PREFIX = _(
    "Error while trying to get the Kanidm minimum credential type"
)
FAILED_TO_KANIDM_LOGIN = _(
    "%(prefix)s: failed to log in to the Kanidm admin account."
) % {"prefix": KANIDM_GET_MIN_CREDENTIAL_TYPE_ERROR_PREFIX}

FAILED_TO_KANIDM_GET_IDM_ALL_PERSONS = _(
    "%(prefix)s: failed to get the full definition of the group idm_all_persons."
) % {"prefix": KANIDM_GET_MIN_CREDENTIAL_TYPE_ERROR_PREFIX}

FAILED_TO_KANIDM_SET_MINIMUM_CREDENTIAL_TYPE = _(
    "Error while trying to set the Kanidm minimum credential type: failed to update the credential_type_minimum policy for the group idm_all_persons."
)


async def get_kanidm_minimum_credential_type() -> KanidmCredentialType:
    kanidm_admin_password = KanidmAdminToken.reset_idm_admin_password()

    with temporary_env_var(key="KANIDM_PASSWORD", value=kanidm_admin_password):
        command = "kanidm login -D idm_admin"

        try:
            proc = await asyncio.create_subprocess_exec(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise KanidmCliSubprocessError(
                    command=command,
                    description=FAILED_TO_KANIDM_LOGIN,
                    error=stderr.decode(errors="replace"),
                )
        except OSError as error:
            raise KanidmCliSubprocessError(
                command=command,
                description=FAILED_TO_KANIDM_LOGIN,
                error=str(error),
            )

        command = "kanidm group get idm_all_persons"
        try:
            proc = await asyncio.create_subprocess_exec(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            output, stderr = await proc.communicate()
            output = output.decode(errors="replace")

            if proc.returncode != 0:
                raise KanidmCliSubprocessError(
                    command=command,
                    description=FAILED_TO_KANIDM_GET_IDM_ALL_PERSONS,
                    error=stderr.decode(errors="replace"),
                )
        except OSError as error:
            raise KanidmCliSubprocessError(
                command=command,
                description=FAILED_TO_KANIDM_GET_IDM_ALL_PERSONS,
                error=str(error),
            )

    regex_pattern = r"(?mi)^\s*credential_type_minimum\s*:\s*(\S+)"
    match = re.search(regex_pattern, output)
    if match and match.group(1):
        return KanidmCredentialType(match.group(1))

    raise FailedToFindResult(
        data=output,
        command=command,
        description=_(
            dedent(
                """
                Kanidm CLI did not return the minimum credential type for the "idm_all_persons" group.
                %(KANIDM_DESCRIPTION)s
                The code searches the command output for a line like:
                "credential_type_minimum: <VALUE>"

                Standard output example:
                %(STANDARD_OUTPUT_EXAMPLE)s

                %(KANIDM_PROBLEMS)s
                """
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "STANDARD_OUTPUT_EXAMPLE": STANDARD_OUTPUT_EXAMPLE,
                "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
            },
        ),
        regex_pattern=regex_pattern,
    )


async def set_kanidm_minimum_credential_type(
    minimum_credential_type: KanidmCredentialType,
) -> None:
    command = [
        "kanidm",
        "group",
        "account-policy",
        "credential-type-minimum",
        "idm_all_persons",
        minimum_credential_type.value,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        output, stderr = await proc.communicate()
        output = output.decode(errors="replace")

        if proc.returncode != 0:
            raise KanidmCliSubprocessError(
                command=" ".join(command),
                description=FAILED_TO_KANIDM_SET_MINIMUM_CREDENTIAL_TYPE,
                error=stderr.decode(errors="replace"),
            )
    except OSError as error:
        raise KanidmCliSubprocessError(
            command=" ".join(command),
            description=FAILED_TO_KANIDM_SET_MINIMUM_CREDENTIAL_TYPE,
            error=str(error),
        )

    if "Updated credential type minimum" not in output:
        raise KanidmCliSubprocessError(
            error=output,
            command=" ".join(command),
            description=dedent(
                _(
                    """
                    Kanidm CLI did not confirm that the minimum credential type was updated.
                    The output does not contain the expected phrase: "Updated credential type minimum".
                    """
                )
            ),
        )

    if await get_kanidm_minimum_credential_type() != minimum_credential_type:
        raise FailedToSetupKanidmMinimumCredentialType()
