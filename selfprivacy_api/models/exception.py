from abc import ABC, abstractmethod

from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
)


class ApiException(Exception, ABC):
    code: int = 400

    @abstractmethod
    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        """
        Translatable error message.

        Example:

        return t.translate(
            text=_(
                dedent(
                    \"\"\"
                    The Kanidm response does not contain a password reset link.
                    Failed to find "token" in data.
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    Endpoint: %(endpoint)s
                    Method: %(method)s
                    Data: %(data)s
                    \"\"\"
                )
                % {
                    "endpoint": self.endpoint,
                    "method": self.method,
                    "data": self.data,
                    "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
                }
            ),
            locale=locale,
        )
        """
