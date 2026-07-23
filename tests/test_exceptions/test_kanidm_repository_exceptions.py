import pytest

from selfprivacy_api.exceptions import (
    REPORT_IT_TO_SUPPORT_CHATS,
)
from selfprivacy_api.exceptions.kanidm import (
    KANIDM_DEBUG_HELP,
    KANIDM_DESCRIPTION,
    KANIDM_PROBLEMS,
)
from selfprivacy_api.exceptions.users.kanidm_repository import (
    FailedToGetValidKanidmToken,
    KanidmCliSubprocessError,
    KanidmDidNotReturnAdminPassword,
    KanidmQueryError,
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
    NoPasswordResetLinkFoundInResponse,
)
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)


@pytest.fixture
def get_domain_mock(mocker):
    return mocker.patch(
        "selfprivacy_api.utils.get_domain",
        return_value="example.org",
    )


def test_kanidm_query_error_get_error_message(get_domain_mock):
    error = KanidmQueryError(
        endpoint="person",
        method="GET",
        error_text={"detail": "boom"},
        description="Custom description",
    )

    message = error.get_error_message()

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )
    assert "Custom description" in message
    assert "Endpoint: https://auth.example.org/v1/person" in message
    assert "GET" in message
    assert "{'detail': 'boom'}" in message


def test_kanidm_return_empty_response_get_error_message():
    error = KanidmReturnEmptyResponse(
        endpoint="group",
        method="POST",
    )

    message = error.get_error_message()

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )
    assert "Endpoint: group" in message
    assert "POST" in message


def test_kanidm_return_unknown_response_type_get_error_message():
    error = KanidmReturnUnknownResponseType(
        endpoint="token",
        method="PATCH",
        response_data=["unexpected", "list"],
    )

    message = error.get_error_message()

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert t.translate(text=KANIDM_PROBLEMS, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )
    assert "Endpoint: token" in message
    assert "PATCH" in message
    assert "['unexpected', 'list']" in message


def test_kanidm_did_not_return_admin_password_get_error_message():
    error = KanidmDidNotReturnAdminPassword(
        command="kanidm recover-account admin",
        output="stdout text",
    )

    message = error.get_error_message()

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert t.translate(text=KANIDM_PROBLEMS, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )
    assert t.translate(text=KANIDM_DEBUG_HELP, locale=DEFAULT_LOCALE) in message
    assert "kanidm recover-account admin" in message
    assert "stdout text" in message


def test_kanidm_cli_subprocess_error_get_error_message():
    error = KanidmCliSubprocessError(
        command="kanidm login",
        error="permission denied",
        description="Token creation failed",
    )

    message = error.get_error_message()

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert t.translate(text=KANIDM_PROBLEMS, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )
    assert "Token creation failed" in message
    assert "kanidm login" in message
    assert "permission denied" in message


def test_failed_to_get_valid_kanidm_token_get_error_message():
    error = FailedToGetValidKanidmToken()

    message = error.get_error_message()

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert t.translate(text=KANIDM_PROBLEMS, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )


def test_no_password_reset_link_found_in_response_get_error_message():
    error = NoPasswordResetLinkFoundInResponse(
        endpoint="reset",
        method="PUT",
        data={"status": "ok"},
    )

    message = error.get_error_message()

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )
    assert "Endpoint: reset" in message
    assert "PUT" in message
    assert "{'status': 'ok'}" in message


def test_kanidm_return_empty_response_get_error_message_with_explicit_locale():
    error = KanidmReturnEmptyResponse(
        endpoint="test",
        method="GET",
    )

    message = error.get_error_message(locale=DEFAULT_LOCALE)

    assert message is not None
    assert isinstance(message, str)
    assert message.strip() != ""

    assert t.translate(text=KANIDM_DESCRIPTION, locale=DEFAULT_LOCALE) in message
    assert (
        t.translate(text=REPORT_IT_TO_SUPPORT_CHATS, locale=DEFAULT_LOCALE) in message
    )
    assert "Endpoint: test" in message
    assert "GET" in message
