import pytest
import subprocess
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)


@pytest.fixture()
def kanidm():
    pass


def test_kanidm_present():
    output = subprocess.check_output(["kanidm", "--help"])
    assert output
