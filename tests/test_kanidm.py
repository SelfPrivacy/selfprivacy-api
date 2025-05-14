import pytest
import subprocess
import os
from os.path import join
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)

DOMAIN = "killersofwords.com"
PORT = 8443


class TestCerts:
    tls_cert: str
    tls_chain: str
    tls_key: str


@pytest.fixture()
def kanidm_environment(tmpdir) -> TestCerts:
    dir = tmpdir
    cert_path = join(dir, "cert.pem")
    key_path = join(dir, "key.pem")
    chain_path = join(dir, "chain.pem")

    TestCerts.tls_cert = cert_path
    TestCerts.tls_chain = chain_path
    TestCerts.tls_key = key_path

    os.environ["KANIDM_DOMAIN"] = DOMAIN
    os.environ["KANIDM_ORIGIN"] = f"https://{DOMAIN}:{PORT}"
    os.environ["KANIDM_DB_PATH"] = str(dir)
    os.environ["KANIDM_TLS_CHAIN"] = chain_path
    os.environ["KANIDM_TLS_KEY"] = key_path
    return TestCerts()


@pytest.fixture()
def certs(tmpdir, kanidm_environment):

    assert dir is not None
    assert mkcert("--help")

    assert subprocess.check_output(["kanidmd", "cert-generate"])

    # assert subprocess.run(["mkcert", "-cert-file", TestCerts, "-key-file", key_path])
    # with open(chain_path, "w") as file:
    #     file.write(make_chain(cert_path))

    for file in [kanidm_environment.tls_chain, kanidm_environment.tls_key]:
        assert os.path.exists(file)


@pytest.fixture()
def kanidm(certs):
    assert subprocess.check_output(["kanidmd", "configtest"])

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
