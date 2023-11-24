import pytest
import typing

from os import path
from unittest.mock import DEFAULT
from tests.conftest import global_data_dir

from selfprivacy_api.utils import get_dkim_key, get_domain
import selfprivacy_api.utils as utils

###############################################################################


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():
        return (
            b'selector._domainkey\tIN\tTXT\t( "v=DKIM1; k=rsa; "\n\t  "p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNn/IhEz1SxgHxxxI8vlPYC2dNueiLe1GC4SYz8uHimC8SDkMvAwm7rqi2SimbFgGB5nccCNOqCkrIqJTCB9vufqBnVKAjshHqpOr5hk4JJ1T/AGQKWinstmDbfTLPYTbU8ijZrwwGeqQLlnXR5nSN0GB9GazheA9zaPsT6PV+aQIDAQAB" )  ; ----- DKIM key selector for test-domain.tld\n',
            None,
        )


class NoFileMock(ProcessMock):
    def communicate():
        return (b"", None)


def _path_exists_with_masked_paths(filepath, masked_paths: typing.List[str]):
    if filepath in masked_paths:
        return False
    else:
        # this will cause the mocker to return the standard path.exists output
        # see https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock.side_effect
        return DEFAULT


def path_exists_func_but_with_masked_paths(masked_paths: typing.List[str]):
    """
    Sometimes we do not want to pretend that no files exist at all, but that only specific files do not exist
    This provides the needed path.exists function for some arbitrary list of masked paths
    """
    return lambda x: _path_exists_with_masked_paths(x, masked_paths)


@pytest.fixture
def mock_all_paths_exist(mocker):
    mock = mocker.patch("os.path.exists", autospec=True, return_value=True)
    return mock


@pytest.fixture
def mock_subproccess_popen_dkimfile(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


@pytest.fixture
def mock_subproccess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=NoFileMock)
    return mock


@pytest.fixture
def domain_file(mocker):
    # TODO: move to conftest. Challenge: it does not behave with "/" like pytest datadir does
    domain_path = path.join(global_data_dir(), "domain")
    mocker.patch("selfprivacy_api.utils.DOMAIN_FILE", domain_path)
    return domain_path


@pytest.fixture
def mock_no_dkim_file(mocker):
    """
    Should have domain mocks
    """
    domain = utils.get_domain()
    # try:
    #     domain = get_domain()
    # except Exception as e:
    #     domain = ""

    masked_files = ["/var/dkim/" + domain + ".selector.txt"]
    mock = mocker.patch(
        "os.path.exists",
        side_effect=path_exists_func_but_with_masked_paths(masked_files),
    )
    return mock


###############################################################################


def test_get_dkim_key(
    mock_subproccess_popen_dkimfile, mock_all_paths_exist, domain_file
):
    """Test DKIM key"""
    dkim_key = get_dkim_key("test-domain.tld")
    assert (
        dkim_key
        == "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNn/IhEz1SxgHxxxI8vlPYC2dNueiLe1GC4SYz8uHimC8SDkMvAwm7rqi2SimbFgGB5nccCNOqCkrIqJTCB9vufqBnVKAjshHqpOr5hk4JJ1T/AGQKWinstmDbfTLPYTbU8ijZrwwGeqQLlnXR5nSN0GB9GazheA9zaPsT6PV+aQIDAQAB"
    )
    assert mock_subproccess_popen_dkimfile.call_args[0][0] == [
        "cat",
        "/var/dkim/test-domain.tld.selector.txt",
    ]


def test_no_dkim_key(
    authorized_client, domain_file, mock_no_dkim_file, mock_subproccess_popen
):
    """Test no DKIM key"""
    dkim_key = get_dkim_key("test-domain.tld")
    assert dkim_key is None
    assert mock_subproccess_popen.called == False
