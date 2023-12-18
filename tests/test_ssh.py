import pytest

from selfprivacy_api.actions.ssh import set_ssh_settings, get_ssh_settings
from selfprivacy_api.utils import WriteUserData, ReadUserData


@pytest.fixture(params=[True, False])
def bool_value(request):
    return request.param


@pytest.fixture(
    params=[
        "normal_populated_json",
        "deleted_enabled",
        "deleted_auth",
        "empty",
        "ssh_not_in_json",
    ]
)
def possibly_undefined_ssh_settings(generic_userdata, request, bool_value):
    with WriteUserData() as data:
        data["ssh"] = {"enable": bool_value, "passswordAuthentication": bool_value}
    assert get_raw_json_ssh_setting("enable") == bool_value
    assert get_raw_json_ssh_setting("passswordAuthentication") == bool_value

    if request.param == "deleted_enabled":
        with WriteUserData() as data:
            del data["ssh"]["enable"]

    if request.param == "deleted_auth":
        with WriteUserData() as data:
            del data["ssh"]["passswordAuthentication"]

    if request.param == "empty":
        with WriteUserData() as data:
            del data["ssh"]["passswordAuthentication"]
            del data["ssh"]["enable"]

    if request.param == "ssh_not_in_json":
        with WriteUserData() as data:
            del data["ssh"]


@pytest.fixture(params=[True, False, None])
def ssh_enable_spectrum(request):
    return request.param


@pytest.fixture(params=[True, False, None])
def password_auth_spectrum(request):
    return request.param


def get_raw_json_ssh_setting(setting: str):
    with ReadUserData() as data:
        return (data.get("ssh") or {}).get(setting)


def test_read_json(possibly_undefined_ssh_settings):
    with ReadUserData() as data:
        if "ssh" not in data.keys():
            assert get_ssh_settings().enable is not None
            assert get_ssh_settings().passwordAuthentication is not None

            # TODO: Is it really a good idea to have password ssh enabled by default?
            assert get_ssh_settings().enable is True
            assert get_ssh_settings().passwordAuthentication is True
            return

        if "enable" not in data["ssh"].keys():
            assert get_ssh_settings().enable is True
        else:
            assert get_ssh_settings().enable == data["ssh"]["enable"]

        if "passwordAuthentication" not in data["ssh"].keys():
            assert get_ssh_settings().passwordAuthentication is True
        else:
            assert (
                get_ssh_settings().passwordAuthentication
                == data["ssh"]["passwordAuthentication"]
            )


def test_enabling_disabling_writes_json(
    possibly_undefined_ssh_settings, ssh_enable_spectrum, password_auth_spectrum
):

    original_enable = get_raw_json_ssh_setting("enable")
    original_password_auth = get_raw_json_ssh_setting("passwordAuthentication")

    set_ssh_settings(ssh_enable_spectrum, password_auth_spectrum)

    with ReadUserData() as data:
        if ssh_enable_spectrum is None:
            assert get_raw_json_ssh_setting("enable") == original_enable
        else:
            assert get_raw_json_ssh_setting("enable") == ssh_enable_spectrum

        if password_auth_spectrum is None:
            assert (
                get_raw_json_ssh_setting("passwordAuthentication")
                == original_password_auth
            )
        else:
            assert (
                get_raw_json_ssh_setting("passwordAuthentication")
                == password_auth_spectrum
            )
