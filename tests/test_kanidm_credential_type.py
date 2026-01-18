from textwrap import dedent

import pytest

from selfprivacy_api.actions.kanidm_credential_type import (
    get_kanidm_minimum_credential_type,
    set_kanidm_minimum_credential_type,
)
from selfprivacy_api.exceptions.kanidm import FailedToSetupKanidmMinimumCredentialType
from selfprivacy_api.exceptions.system import FailedToFindResult
from selfprivacy_api.exceptions.users.kanidm_repository import KanidmCliSubprocessError
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType

STANDARD_OUTPUT_EXAMPLE = dedent(
    """
    name: idm_all_persons
    uuid: 00000000-0000-0000-0000-000000000000
    description: All persons
    credential_type_minimum: any
    """
)


class Proc:
    def __init__(self, stdout=b"", stderr=b"", returncode=0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr


@pytest.mark.asyncio
async def test_get_kanidm_credential_type(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.KanidmAdminToken.reset_idm_admin_password",
        return_value="dummy",
    )

    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.asyncio.create_subprocess_exec",
        side_effect=[
            Proc(stdout=b"login ok\n", returncode=0),
            Proc(stdout=STANDARD_OUTPUT_EXAMPLE.encode(), returncode=0),
        ],
    )

    assert await get_kanidm_minimum_credential_type() == KanidmCredentialType.any


@pytest.mark.asyncio
async def test_set_kanidm_credential_type(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.asyncio.create_subprocess_exec",
        return_value=Proc(stdout=b"Updated credential type minimum\n", returncode=0),
    )

    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.get_kanidm_minimum_credential_type",
        return_value=KanidmCredentialType.passkey,
    )

    await set_kanidm_minimum_credential_type(KanidmCredentialType.passkey)


@pytest.mark.asyncio
async def test_get_kanidm_credential_type_login_oserror(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.KanidmAdminToken.reset_idm_admin_password",
        return_value="dummy",
    )
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.asyncio.create_subprocess_exec",
        side_effect=OSError("no such file or directory"),
    )

    with pytest.raises(KanidmCliSubprocessError):
        await get_kanidm_minimum_credential_type()


@pytest.mark.asyncio
async def test_get_kanidm_credential_type_missing_field_raises_failed_to_find_result(
    mocker,
):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.KanidmAdminToken.reset_idm_admin_password",
        return_value="dummy",
    )
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.asyncio.create_subprocess_exec",
        side_effect=[
            Proc(stdout=b"login ok\n", returncode=0),
            Proc(
                stdout=dedent(
                    """
                    name: idm_all_persons
                    uuid: 00000000-0000-0000-0000-000000000000
                    description: All persons
                    """
                ).encode(),
                returncode=0,
            ),
        ],
    )

    with pytest.raises(FailedToFindResult):
        await get_kanidm_minimum_credential_type()


@pytest.mark.asyncio
async def test_set_kanidm_credential_type_subprocess_returncode_nonzero(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.asyncio.create_subprocess_exec",
        return_value=Proc(stderr=b"failed\n", returncode=1),
    )

    with pytest.raises(KanidmCliSubprocessError):
        await set_kanidm_minimum_credential_type(KanidmCredentialType.passkey)


@pytest.mark.asyncio
async def test_set_kanidm_credential_type_subprocess_oserror(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.asyncio.create_subprocess_exec",
        side_effect=OSError("exec format error"),
    )

    with pytest.raises(KanidmCliSubprocessError):
        await set_kanidm_minimum_credential_type(KanidmCredentialType.passkey)


@pytest.mark.asyncio
async def test_set_kanidm_credential_type_verification_mismatch_raises(mocker):
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.asyncio.create_subprocess_exec",
        return_value=Proc(stdout=b"Updated credential type minimum\n", returncode=0),
    )
    mocker.patch(
        "selfprivacy_api.actions.kanidm_credential_type.get_kanidm_minimum_credential_type",
        return_value=KanidmCredentialType.any,
    )

    with pytest.raises(FailedToSetupKanidmMinimumCredentialType):
        await set_kanidm_minimum_credential_type(KanidmCredentialType.passkey)
