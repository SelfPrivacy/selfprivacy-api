import gettext
import logging
from textwrap import dedent

from selfprivacy_api.exceptions import (
    REPORT_IT_TO_SUPPORT_CHATS,
)
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

logger = logging.getLogger(__name__)

_ = gettext.gettext


KANIDM_DESCRIPTION = _(
    "Kanidm is the identity and authentication service that manages users and access to system services."
)

KANIDM_PROBLEMS = _(
    "In some cases, a Kanidm update may introduce breaking changes affecting the API, CLI commands, or configuration compatibility."
)

KANIDM_DEBUG_HELP = _(
    dedent(
        """
        Console commands to debug:
            "systemctl status kanidm.service"
            "journalctl -u kanidm.service -f"
        """
    )
)

STANDARD_OUTPUT_EXAMPLE = dedent(
    """
    name: idm_all_persons
    uuid: 00000000-0000-0000-0000-000000000000
    description: All persons
    credential_type_minimum: any
    """
)


class FailedToSetupKanidmMinimumCredentialType(AbstractException):
    """
    The minimum credential type update was executed, but verification failed.
    """

    code: int = 500

    SET_COMMAND_TEMPLATE = "kanidm group account-policy credential-type-minimum idm_all_persons <CREDENTIAL_TYPE>"
    GET_COMMAND = "kanidm group get idm_all_persons"
    GET_REGEX_PATTERN = r"(?mi)^\s*credential_type_minimum\s*:\s*(\S+)"
    EXPECTED_CONFIRMATION_PHRASE = "Updated credential type minimum"

    def __init__(self, log: bool = True):
        if log:
            logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Kanidm settings were not applied.
                    The system tried to set the minimum credential type for the "idm_all_persons" group,
                    but verification failed: the value read back from Kanidm does not match the value that was requested.
                    %(KANIDM_DESCRIPTION)s
                    %(KANIDM_PROBLEMS)s

                    %(REPORT_IT_TO_SUPPORT_CHATS)s

                    Set command (template): %(set_command_template)s
                    Expected confirmation phrase: %(expected_phrase)s
                    Get command: %(get_command)s
                    Used regex pattern: %(regex_pattern)s

                    Standard output example:
                    %(STANDARD_OUTPUT_EXAMPLE)s
                    """
                )
            )
            % {
                "set_command_template": self.SET_COMMAND_TEMPLATE,
                "expected_phrase": self.EXPECTED_CONFIRMATION_PHRASE,
                "get_command": self.GET_COMMAND,
                "regex_pattern": self.GET_REGEX_PATTERN,
                "KANIDM_DESCRIPTION": KANIDM_DESCRIPTION,
                "KANIDM_PROBLEMS": KANIDM_PROBLEMS,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                "STANDARD_OUTPUT_EXAMPLE": STANDARD_OUTPUT_EXAMPLE,
            },
            locale=locale,
        )
