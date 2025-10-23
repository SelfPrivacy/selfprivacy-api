import pytest
from selfprivacy_api.utils import ReadUserData, UserDataFiles

from selfprivacy_api.actions.system import run_blocking, ShellException
from selfprivacy_api.actions.system import set_dns_provider
from selfprivacy_api.graphql.queries.providers import DnsProvider


def assert_provider(provider_str: str, key: str):
    with ReadUserData() as user_data:
        assert user_data["dns"]["provider"] == provider_str
    with ReadUserData(file_type=UserDataFiles.SECRETS) as secrets:
        assert secrets["dns"]["apiKey"] == key


def test_set_dns(generic_userdata):
    token = "testytesty"
    provider = DnsProvider.DESEC

    set_dns_provider(provider, token)

    assert_provider(provider.value, token)


# uname is just an arbitrary command expected to be everywhere we care
def test_uname():
    output = run_blocking(["uname"])
    assert output is not None


def test_uname_new_session():
    output = run_blocking(["uname"], new_session=True)
    assert output is not None


def test_uname_nonexistent_args():
    with pytest.raises(ShellException) as exc:
        run_blocking(["uname", "isdyfhishfaisljhkeysmash"], new_session=True)
    assert "extra operand" in (exc.value.output or "").lower()
