import pytest

from selfprivacy_api.actions.kanidm_credential_type import (
    get_kanidm_minimum_credential_type,
    set_kanidm_minimum_credential_type,
)
from selfprivacy_api.exceptions.kanidm import KanidmQueryError
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType


@pytest.mark.asyncio
async def test_get_kanidm_credential_type(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.send_kanidm_query",
        return_value=["any"],
    )

    assert await get_kanidm_minimum_credential_type() == KanidmCredentialType.any


@pytest.mark.asyncio
async def test_get_kanidm_credential_type_query_error(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.send_kanidm_query",
        side_effect=KanidmQueryError(
            endpoint="group/idm_all_persons/_attr/credential_type_minimum",
            method="GET",
            error_text="failed",
        ),
    )

    with pytest.raises(KanidmQueryError):
        await get_kanidm_minimum_credential_type()


@pytest.mark.asyncio
async def test_set_kanidm_credential_type(mocker):
    send_query = mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.send_kanidm_query",
        return_value={"status": "ok"},
    )
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.get_kanidm_minimum_credential_type",
        return_value=KanidmCredentialType.passkey,
    )

    await set_kanidm_minimum_credential_type(KanidmCredentialType.passkey)
    send_query.assert_called_once_with(
        endpoint="group/idm_all_persons/_attr/credential_type_minimum",
        method="PUT",
        data=["passkey"],
    )


@pytest.mark.asyncio
async def test_get_kanidm_credential_type_missing_field_raises_kanidm_query_error(
    mocker,
):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.send_kanidm_query",
        return_value=[],
    )

    with pytest.raises(KanidmQueryError):
        await get_kanidm_minimum_credential_type()


@pytest.mark.asyncio
async def test_set_kanidm_credential_type_query_error(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.send_kanidm_query",
        side_effect=KanidmQueryError(
            endpoint="group/idm_all_persons/_attr/credential_type_minimum",
            method="PUT",
            error_text="failed",
        ),
    )

    with pytest.raises(KanidmQueryError):
        await set_kanidm_minimum_credential_type(KanidmCredentialType.passkey)
