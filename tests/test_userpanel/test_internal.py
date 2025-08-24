import pytest

import asyncio

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request

from selfprivacy_api.userpanel.routes.internal import (
    check_email_password,
    EmailPasswordCheckInput,
)


@pytest.fixture
def get_domain_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.userpanel.routes.internal.get_domain",
        # "selfprivacy_api.utils.get_domain",
        autospec=True,
        return_value="test.domain",
    )
    return mock


def test_check_email_password(get_domain_mock):
    input_data = EmailPasswordCheckInput(username="tester", password="iloveyou")

    assert isinstance(
        asyncio.run(
            check_email_password(
                request=Request({"type": "http"}), input_data=input_data
            )
        ),
        JSONResponse({"isValid": True}),
    )


def test_check_email_password_with_at_in_username(get_domain_mock):
    input_data = EmailPasswordCheckInput(
        username="tester@test.domain", password="iloveyou"
    )

    assert isinstance(
        asyncio.run(
            check_email_password(
                request=Request({"type": "http"}), input_data=input_data
            )
        ),
        JSONResponse({"isValid": True}),
    )


def test_check_email_password_with_at_in_username_wrong_domain(get_domain_mock):
    input_data = EmailPasswordCheckInput(
        username="tester@wrong.domain", password="iloveyou"
    )

    assert isinstance(
        asyncio.run(
            check_email_password(
                request=Request({"type": "http"}), input_data=input_data
            )
        ),
        JSONResponse({"isValid": False}),
    )


def test_check_email_password_without_username(get_domain_mock):
    input_data = EmailPasswordCheckInput(username="", password="iloveyou")

    assert isinstance(
        asyncio.run(
            check_email_password(
                request=Request({"type": "http"}), input_data=input_data
            )
        ),
        JSONResponse({"isValid": False}),
    )


def test_check_email_password_without_password(get_domain_mock):
    input_data = EmailPasswordCheckInput(username="tester", password="")

    assert isinstance(
        asyncio.run(
            check_email_password(
                request=Request({"type": "http"}), input_data=input_data
            )
        ),
        JSONResponse({"isValid": False}),
    )
