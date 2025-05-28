import pytest
import subprocess
from subprocess import STDOUT, TimeoutExpired, CalledProcessError
import os
from os.path import join
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)

DOMAIN = "killersofwords.com"
PORT = 8443
ENV_KEY = "NIX_SSL_CERT_FILE"


class TestCerts:
    tls_cert: str
    tls_chain: str
    tls_key: str


@pytest.fixture()
def dns():
    with open("/etc/resolv.conf", "a") as file:
        file.write(f"\n search {DOMAIN}\n")
        file.flush()
    with open("/etc/resolv.conf", "r") as file:
        assert DOMAIN in file.read()


@pytest.fixture()
def kanidm_environment(tmpdir) -> TestCerts:
    dir = tmpdir
    cert_path = join(dir, "cert.pem")
    key_path = join(dir, "key.pem")
    chain_path = join(dir, "chain.pem")
    db_path = join(dir, "kanidm.db")

    kanidmd_sockdir = "/run/kanidmd"
    if not os.path.exists(kanidmd_sockdir):
        os.mkdir(kanidmd_sockdir)
    with open(join(kanidmd_sockdir, "sock"), "w") as file:
        file.flush()

    TestCerts.tls_cert = cert_path
    TestCerts.tls_chain = chain_path
    TestCerts.tls_key = key_path

    os.environ["KANIDM_DOMAIN"] = DOMAIN
    os.environ["KANIDM_ORIGIN"] = f"https://{DOMAIN}:{PORT}"
    os.environ["KANIDM_DB_PATH"] = db_path
    os.environ["KANIDM_TLS_CHAIN"] = chain_path
    os.environ["KANIDM_TLS_KEY"] = key_path
    return TestCerts()


@pytest.fixture()
def certs(tmpdir, kanidm_environment):

    backup_certfile = None
    if ENV_KEY in os.environ:
        backup_certfile = os.environ[ENV_KEY]

    assert mkcert("--help")

    assert subprocess.check_output(["kanidmd", "cert-generate"])

    # assert subprocess.run(["mkcert", "-cert-file", TestCerts, "-key-file", key_path])
    # with open(chain_path, "w") as file:
    #     file.write(make_chain(cert_path))

    for file in [kanidm_environment.tls_chain, kanidm_environment.tls_key]:
        assert os.path.exists(file)

    with open(kanidm_environment.tls_chain) as file:
        lines = file.readlines()
    lines = [l.strip() for l in lines]

    separator = "-----BEGIN CERTIFICATE-----"
    separator2 = "-----END CERTIFICATE-----"
    assert lines.count(separator) == 2
    assert lines.count(separator2) == 2

    # we need the second one bc apparently in chain
    # the first one is the actual cert
    # and the last one is root

    begin = lines.index(separator, lines.index(separator2))
    rootcert = lines[begin:]
    assert rootcert.count(separator) == 1
    assert rootcert.count(separator2) == 1
    assert len(rootcert) > 2

    cadir = tmpdir
    cafile = join(cadir, "ca-certificates.crt")
    os.environ[ENV_KEY] = cafile

    assert not os.path.exists(cafile)

    with open(cafile, "w") as file:
        file.writelines("\n".join(rootcert))
        file.flush()
    with open(cafile, "r") as file:
        allcerts = file.read()
        for line in rootcert:
            assert line in allcerts

    assert "OK" in subprocess.check_output(["openssl", "verify", cafile]).decode(
        "utf-8"
    )

    yield

    # restoring env
    if not backup_certfile:
        del os.environ[ENV_KEY]
    else:
        os.environ[ENV_KEY] = backup_certfile


from time import sleep


def inspect_file(path: str):
    with open(path) as file:
        raise ValueError(file.read())


def test_kanidm_present():
    output = subprocess.check_output(["kanidm", "--help"])
    assert output


@pytest.fixture()
def kanidm(certs, dns):
    assert subprocess.check_output(["kanidmd", "configtest"])
    command = ["kanidmd", "server"]

    # First assert that consumer does not fail by itself
    # Idk yet how to do it more elegantly
    try:
        subprocess.check_output(command, timeout=2)
    except TimeoutExpired:
        pass

    # Then open it for real
    handle = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    sleep(2)
    origin = os.environ["KANIDM_ORIGIN"]

    # check that it works
    test_output = subprocess.check_output(
        ["curl", "-v", origin + "/status"], stderr=STDOUT
    ).decode("utf-8")
    assert "SSL certificate verify ok" in test_output
    test_output = subprocess.check_output(
        ["curl", "-s", origin + "/status"], stderr=STDOUT
    ).decode("utf-8")
    assert "true" in test_output

    yield handle

    handle.kill()


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
