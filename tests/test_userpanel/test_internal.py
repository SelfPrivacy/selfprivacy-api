import pytest

import json
import asyncio
from passlib.hash import sha512_crypt

from fastapi.responses import JSONResponse
from fastapi import Request

from selfprivacy_api.userpanel.routes.internal import (
    check_email_password,
    EmailPasswordCheckInput,
)
from selfprivacy_api.models.email_password_metadata import EmailPasswordData


@pytest.fixture
def get_domain_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.userpanel.routes.internal.get_domain",
        autospec=True,
        return_value="test.domain",
    )
    return mock


@pytest.fixture
def get_all_email_passwords_metadata_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.repositories.email_password.email_password_redis_repository.EmailPasswordManager.get_all_email_passwords_metadata",
        autospec=True,
        return_value=[
            EmailPasswordData(
                uuid="tester",
                display_name="tester",
                password=sha512_crypt.hash("iloveyou"),
            )
        ],
    )
    return mock


@pytest.mark.asyncio
async def test_check_email_password(
    get_domain_mock, get_all_email_passwords_metadata_mock
):
    input_data = EmailPasswordCheckInput(username="tester", password="iloveyou")

    reply = await check_email_password(
        request=Request({"type": "http"}), input_data=input_data
    )

    assert isinstance(reply, JSONResponse)
    assert json.loads(reply.body.decode()) == {"isValid": False}


@pytest.mark.asyncio
async def test_check_email_password_with_at_in_username(
    get_domain_mock, get_all_email_passwords_metadata_mock
):
    input_data = EmailPasswordCheckInput(
        username="tester@test.domain", password="iloveyou"
    )

    reply = await check_email_password(
        request=Request({"type": "http"}), input_data=input_data
    )

    assert isinstance(reply, JSONResponse)
    assert json.loads(reply.body.decode()) == {"isValid": True}


@pytest.mark.asyncio
async def test_check_email_password_with_at_in_username_wrong_domain(
    get_domain_mock, get_all_email_passwords_metadata_mock
):
    input_data = EmailPasswordCheckInput(
        username="tester@wrong.domain", password="iloveyou"
    )

    reply = await check_email_password(
        request=Request({"type": "http"}), input_data=input_data
    )

    assert isinstance(reply, JSONResponse)
    assert json.loads(reply.body.decode()) == {"isValid": False}


@pytest.mark.asyncio
async def test_check_email_password_without_username(
    get_domain_mock, get_all_email_passwords_metadata_mock
):
    input_data = EmailPasswordCheckInput(username="", password="iloveyou")
    reply = await check_email_password(
        request=Request({"type": "http"}), input_data=input_data
    )

    assert isinstance(reply, JSONResponse)
    assert json.loads(reply.body.decode()) == {"isValid": False}


@pytest.mark.asyncio
async def test_check_email_password_without_password(
    get_domain_mock, get_all_email_passwords_metadata_mock
):
    input_data = EmailPasswordCheckInput(username="tester", password="")

    reply = await check_email_password(
        request=Request({"type": "http"}), input_data=input_data
    )

    assert isinstance(reply, JSONResponse)
    assert json.loads(reply.body.decode()) == {"isValid": False}
