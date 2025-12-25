from abc import ABC, abstractmethod

from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
)


class ApiException(Exception, ABC):
    """
    SelfPrivacy API standard for Exceptions.


    Example of __init__:

        def __init__(self, log: bool = True, regex_pattern: str, output: Any):
            self.regex_pattern = regex_pattern
            self.output = str(output)

            if log:
                logger.error(self.get_error_message())
    """

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
                    dedent(
                        \"\"\"
                        Something is wrong with the user management program Kanidm.
                        Kanidm CLI did not return the admin password.
                        %(maybe_kanidm_broke_compatibility)s
                        %(REPORT_IT_TO_SUPPORT_CHATS)s
                        Used command: %(command)s
                        Used regex pattern: %(regex_pattern)s
                        Kanidm's CLI output: %(output)s
                        \"\"\"
                    )
                )
                % {
                    "command": self.command,
                    "regex_pattern": self.regex_pattern,
                    "output": self.output,
                    "maybe_kanidm_broke_compatibility": KANIDM_BROKE_COMPATIBILITY,
                    "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                },
                locale=locale,
            )
        """
