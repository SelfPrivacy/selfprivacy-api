import pytest

import os
from os import path
from tests.conftest import global_data_dir

from selfprivacy_api.utils import get_dkim_key, get_domain

###############################################################################

DKIM_FILE_CONTENT = b'selector._domainkey\tIN\tTXT\t( "v=DKIM1; k=rsa; "\n\t  "p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNn/IhEz1SxgHxxxI8vlPYC2dNueiLe1GC4SYz8uHimC8SDkMvAwm7rqi2SimbFgGB5nccCNOqCkrIqJTCB9vufqBnVKAjshHqpOr5hk4JJ1T/AGQKWinstmDbfTLPYTbU8ijZrwwGeqQLlnXR5nSN0GB9GazheA9zaPsT6PV+aQIDAQAB" )  ; ----- DKIM key selector for test-domain.tld\n'


@pytest.fixture
def dkim_file(mocker, tmpdir, generic_userdata):
    domain = get_domain()
    assert domain is not None
    assert domain != ""
    # In a separate folder to not interfere with dkim backups
    dkim_dir = path.join(tmpdir, "dkim")
    os.mkdir(dkim_dir)

    filename = domain + ".selector.txt"
    dkim_path = path.join(dkim_dir, filename)

    with open(dkim_path, "wb") as file:
        file.write(DKIM_FILE_CONTENT)

    mocker.patch("selfprivacy_api.utils.DKIM_DIR", dkim_dir)
    mocker.patch("selfprivacy_api.services.DKIM_DIR", dkim_dir)
    return dkim_path


@pytest.fixture
def no_dkim_file(dkim_file):
    os.remove(dkim_file)
    assert path.exists(dkim_file) is False
    return dkim_file


###############################################################################


def test_get_dkim_key(dkim_file):
    """Test DKIM key"""
    dkim_key = get_dkim_key("test-domain.tld")
    assert (
        dkim_key
        == "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNn/IhEz1SxgHxxxI8vlPYC2dNueiLe1GC4SYz8uHimC8SDkMvAwm7rqi2SimbFgGB5nccCNOqCkrIqJTCB9vufqBnVKAjshHqpOr5hk4JJ1T/AGQKWinstmDbfTLPYTbU8ijZrwwGeqQLlnXR5nSN0GB9GazheA9zaPsT6PV+aQIDAQAB"
    )


def test_no_dkim_key(no_dkim_file):
    """Test no DKIM key"""
    dkim_key = get_dkim_key("test-domain.tld")
    assert dkim_key is None
