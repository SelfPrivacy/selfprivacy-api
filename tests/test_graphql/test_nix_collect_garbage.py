# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import pytest
import strawberry

from selfprivacy_api.jobs import JobStatus, Jobs
from selfprivacy_api.graphql import schema


from selfprivacy_api.jobs.nix_collect_garbage import (
    get_dead_packages,
    parse_line,
    CLEAR_COMPLETED,
    COMPLETED_WITH_ERROR,
    stream_process,
    RESULT_WAS_NOT_FOUND_ERROR,
)

pytest_plugins = ("pytest_asyncio",)


OUTPUT_PRINT_DEAD = """
finding garbage collector roots...
determining live/dead paths...
/nix/store/02k8pmw00p7p7mf2dg3n057771w7liia-python3.10-cchardet-2.1.7
/nix/store/03vc6dznx8njbvyd3gfhfa4n5j4lvhbl-python3.10-async-timeout-4.0.2
/nix/store/03ybv2dvfk7c3cpb527y5kzf6i35ch41-python3.10-pycparser-2.21
/nix/store/04dn9slfqwhqisn1j3jv531lms9w5wlj-python3.10-hypothesis-6.50.1.drv
/nix/store/04hhx2z1iyi3b48hxykiw1g03lp46jk7-python-remove-bin-bytecode-hook
"""


OUTPUT_COLLECT_GARBAGE = """
removing old generations of profile /nix/var/nix/profiles/per-user/def/channels
finding garbage collector roots...
deleting garbage...
deleting '/nix/store/02k8pmw00p7p7mf2dg3n057771w7liia-python3.10-cchardet-2.1.7'
deleting '/nix/store/03vc6dznx8njbvyd3gfhfa4n5j4lvhbl-python3.10-async-timeout-4.0.2'
deleting '/nix/store/03ybv2dvfk7c3cpb527y5kzf6i35ch41-python3.10-pycparser-2.21'
deleting '/nix/store/04dn9slfqwhqisn1j3jv531lms9w5wlj-python3.10-hypothesis-6.50.1.drv'
deleting '/nix/store/04hhx2z1iyi3b48hxykiw1g03lp46jk7-python-remove-bin-bytecode-hook'
deleting unused links...
note: currently hard linking saves -0.00 MiB
190 store paths deleted, 425.51 MiB freed
"""

OUTPUT_COLLECT_GARBAGE_ZERO_TRASH = """
removing old generations of profile /nix/var/nix/profiles/per-user/def/profile
removing old generations of profile /nix/var/nix/profiles/per-user/def/channels
finding garbage collector roots...
deleting garbage...
deleting unused links...
note: currently hard linking saves 0.00 MiB
0 store paths deleted, 0.00 MiB freed
"""

OUTPUT_RUN_NIX_STORE_PRINT_DEAD_ZERO_TRASH = """
finding garbage collector roots...
determining live/dead paths...
"""

log_event = []


@pytest.fixture
def mock_set_job_status(mocker):
    mock = mocker.patch(
        "selfprivacy_api.jobs.nix_collect_garbage.set_job_status_wrapper",
        autospec=True,
        return_value=set_job_status,
    )
    return mock


@pytest.fixture
def job_reset():
    Jobs.reset()


# ---


def test_parse_line(job_reset):
    txt = "190 store paths deleted, 425.51 MiB freed"
    output = (
        JobStatus.FINISHED,
        100,
        CLEAR_COMPLETED,
        "425.51 MiB have been cleared",
    )
    assert parse_line(txt) == output


def test_parse_line_with_blank_line(job_reset):
    txt = ""
    output = (
        JobStatus.FINISHED,
        100,
        COMPLETED_WITH_ERROR,
        RESULT_WAS_NOT_FOUND_ERROR,
    )
    assert parse_line(txt) == output


def test_get_dead_packages(job_reset):
    assert get_dead_packages(OUTPUT_PRINT_DEAD) == (5, 20.0)


def test_get_dead_packages_zero(job_reset):
    assert get_dead_packages("") == (0, 0)


RUN_NIX_COLLECT_GARBAGE_QUERY = """
mutation CollectGarbage {
    system {
        nixCollectGarbage {
            success
            message
            code
        }
    }
}
"""


def test_graphql_nix_collect_garbage(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": RUN_NIX_COLLECT_GARBAGE_QUERY,
        },
    )

    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert response.json()["data"]["system"]["nixCollectGarbage"]["success"] is True
    assert response.json()["data"]["system"]["nixCollectGarbage"]["message"] is not None
    assert response.json()["data"]["system"]["nixCollectGarbage"]["success"] == True
    assert response.json()["data"]["system"]["nixCollectGarbage"]["code"] == 200
