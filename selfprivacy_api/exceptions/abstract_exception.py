import logging
from abc import ABC, abstractmethod

from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
)

logger = logging.getLogger(__name__)


class AbstractException(Exception, ABC):
    """
    SelfPrivacy API standard for Exceptions.

    Example of __init__:

        def __init__(self, log: bool = True, regex_pattern: str, output: Any):
            super().__init__()

            self.regex_pattern = regex_pattern
            self.output = str(output)
    """

    def __init__(self, log: bool = True):
        super().__init__()

        if log:
            logger.error(self.get_error_message())

    # HTTP status code to return
    code: int = 400

    @abstractmethod
    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        """
        Return a translatable error message.

        Error message style guide (3 parts)

        1. User-friendly explanation
        Explain what happened in simple words for a non-technical user.
        If possible, hint at why it happened and how to avoid it next time.

        Goal: the user can often resolve the issue on their own.

        2. Technical details
        Include the data needed to debug the issue as much as possible.
        Ask yourself: "What do I need to fix this?"
        Examples: command, output, regex pattern, etc.

        3. What to do next
        Suggest first steps to resolve the problem.
        It can be a system update or daemon reload.
        For all system problems, include REPORT_IT_TO_SUPPORT_CHATS
        from selfprivacy_api.utils.strings.


        General rules:
        - Save user's and developer's time.
        - Clarity over friendliness. Do not hide errors.
        - Provide as much information as you can.


        Example:

            return t.translate(
                text=_(
                    "Something is wrong with the user management program Kanidm.\n"
                    "Kanidm CLI did not return the admin password.\n"
                    "%(maybe_kanidm_broke_compatibility)s\n"
                    "%(REPORT_IT_TO_SUPPORT_CHATS)s\n"
                    "Used command: %(command)s\n"
                    "Used regex pattern: %(regex_pattern)s\n"
                    "Kanidm's CLI output: %(output)s"
                )
                % {
                    "command": self.command,
                    "regex_pattern": self.regex_pattern,
                    "output": self.output,
                    "maybe_kanidm_broke_compatibility": KANIDM_PROBLEMS,
                    "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                },
                locale=locale,
            )
        """
