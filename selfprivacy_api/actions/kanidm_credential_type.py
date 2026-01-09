import gettext
import logging
import re
import subprocess
from textwrap import dedent

from selfprivacy_api.exceptions import KANIDM_DESCRIPTION, KANIDM_PROBLEMS
from selfprivacy_api.exceptions.kanidm import FailedToSetupKanidmMinimumCredentialType
from selfprivacy_api.exceptions.system import FailedToFindResult, ShellException
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType

logger = logging.getLogger(__name__)

_ = gettext.gettext

# TODO: admin token


async def get_kanidm_minimum_credential_type() -> KanidmCredentialType:
    command_array = ["kanidm", "group", "get", "idm_all_persons"]
    result = subprocess.check_output(
        command_array,
        stderr=subprocess.STDOUT,
        text=True,
    )

    regex_pattern = r"(?mi)^\s*credential_type_minimum\s*:\s*(\S+)"
    match = re.search(regex_pattern, result)
    if match and match.group(1):
        return KanidmCredentialType(match.group(1))

    raise FailedToFindResult(
        data=result,
        command=" ".join(command_array),
        description=dedent(
            _(
                """
                Kanidm CLI did not return the minimum credential type for the "idm_all_persons" group.
                %(KANIDM_DESCRIPTION)s
                The code searches the command output for a line like:
                "credential_type_minimum: <VALUE>"

                Standard output example:
                name: idm_all_persons
                uuid: 00000000-0000-0000-0000-000000000000
                description: All persons
                credential_type_minimum: any

                %(KANIDM_PROBLEMS)s
                """
            )
            % {
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
            },
        ),
        regex_pattern=regex_pattern,
    )


async def set_kanidm_minimum_credential_type(
    minimum_credential_type: KanidmCredentialType,
) -> None:
    command_array = [
        "kanidm",
        "group",
        "account-policy",
        "credential-type-minimum",
        "idm_all_persons",
        minimum_credential_type.value,
    ]

    try:
        result = subprocess.check_output(
            command_array,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        raise ShellException(
            command=" ".join(command_array),
            output=error.output,
            description=dedent(
                _(
                    """
                    Failed to set the minimum credential type for the "idm_all_persons" group in Kanidm.
                    %(KANIDM_DESCRIPTION)s
                    The system tried to update the "idm_all_persons" group policy, but the Kanidm CLI command failed.
                    %(KANIDM_PROBLEMS)s
                    """
                )
                % {
                    "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                    "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
                },
            ),
        )

    if "Updated credential type minimum" not in result:
        raise ShellException(
            command=" ".join(command_array),
            output=result,
            description=dedent(
                _(
                    """
                    Kanidm CLI did not confirm that the minimum credential type was updated.
                    %(KANIDM_DESCRIPTION)s
                    The output does not contain the expected phrase: "Updated credential type minimum".
                    %(KANIDM_PROBLEMS)s
                    """
                )
            ),
        )

    if await get_kanidm_minimum_credential_type() != minimum_credential_type:
        raise FailedToSetupKanidmMinimumCredentialType()
