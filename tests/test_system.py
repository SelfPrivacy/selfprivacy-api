from selfprivacy_api.utils import ReadUserData, UserDataFiles
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
