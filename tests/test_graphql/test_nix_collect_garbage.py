# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import pytest
from selfprivacy_api.utils.huey import huey

from selfprivacy_api.jobs import JobStatus, Jobs, Job
from tests.test_graphql.common import get_data, assert_errorcode, assert_ok, assert_empty

from selfprivacy_api.jobs.nix_collect_garbage import (
    get_dead_packages,
    parse_line,
    CLEAR_COMPLETED,
    COMPLETED_WITH_ERROR,
    RESULT_WAS_NOT_FOUND_ERROR,
    ShellException,
)

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

log_event = []


@pytest.fixture
def mock_delete_old_gens_and_return_dead_report(mocker):
    mock = mocker.patch("selfprivacy_api.jobs.nix_collect_garbage.delete_old_gens_and_return_dead_report", autospec=True, return_value=OUTPUT_PRINT_DEAD)
    return mock


# ---


def test_parse_line():
    txt = "note: currently hard linking saves -0.00 MiB 190 store paths deleted, 425.51 MiB freed"

    job = Jobs.add(
        name="name",
        type_id="parse_line",
        description="description",
    )

    output = parse_line(job, txt)
    assert output.result == '425.51 MiB have been cleared'
    assert output.status == JobStatus.FINISHED
    assert output.error is None


def test_parse_line_with_blank_line():
    txt = ""
    job = Jobs.add(
        name="name",
        type_id="parse_line",
        description="description",
    )

    with pytest.raises(ShellException):
        output = parse_line(job, txt)
    


def test_get_dead_packages():
    assert get_dead_packages(OUTPUT_PRINT_DEAD) == (5, 20.0)


def test_get_dead_packages_zero():
    assert get_dead_packages("") == (0, 0)


RUN_NIX_COLLECT_GARBAGE_MUTATION = """
mutation CollectGarbage {
    system {
        nixCollectGarbage {
            success
            message
            code
            job {
                uid,
                typeId,
                name,
                description,
                status,
                statusText,
                progress,
                createdAt,
                updatedAt,
                finishedAt,
                error,
                result,
            }
        }
    }
}
"""


def test_graphql_nix_collect_garbage(authorized_client, mock_delete_old_gens_and_return_dead_report):
    assert huey.immediate is True
    response = authorized_client.post(
        "/graphql",
        json={
            "query": RUN_NIX_COLLECT_GARBAGE_MUTATION,
        },
    )

    output = get_data(response)["system"]["nixCollectGarbage"]
    assert_ok(output)
    assert output["job"] is not None
    assert output["job"]["status"] == "FINISHED"
    assert output["job"]["error"] is None


def test_graphql_nix_collect_garbage_not_authorized_client(client, mock_delete_old_gens_and_return_dead_report):
    assert huey.immediate is True
    response = client.post(
        "/graphql",
        json={
            "query": RUN_NIX_COLLECT_GARBAGE_MUTATION,
        },
    )

    assert_empty(response)
