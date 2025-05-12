import pytest
import subprocess
from os.path import join
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)


class TestCerts:
    cert: str
    chain: str
    key: str


@pytest.fixture()
def certs(tmpdir) -> TestCerts:
    dir = tmpdir

    assert dir is not None
    assert mkcert("--help")

    cert_path = join(dir, "cert.pem")
    key_path = join(dir, "key.pem")
    chain_path = join(dir, "chain.pem")

    assert subprocess.run(["mkcert", "-cert-file", cert_path, "-key-file", key_path])
    with open(chain_path, "w") as file:
        file.write(make_chain(cert_path))

    TestCerts.cert = cert_path
    TestCerts.chain = chain_path
    TestCerts.key = key_path
    return TestCerts()


@pytest.fixture()
def kanidm(certs):
    pass


def test_kanidm_starts(kanidm):
    pass


def mkcert(arg: str) -> str:
    return subprocess.check_output(["mkcert", arg]).decode("utf-8").strip()


def make_chain(cert_file: str) -> str:
    mkcert("-install")
    ca_dir = mkcert("-CAROOT")
    assert ca_dir

    ca = join(ca_dir, "rootCA.pem")

    with open(ca) as file:
        ca_cert = file.read()

    return ca_cert


def test_kanidm_present():
    output = subprocess.check_output(["kanidm", "--help"])
    assert output
