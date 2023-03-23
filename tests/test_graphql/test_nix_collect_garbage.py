# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import pytest
from selfprivacy_api.jobs import JobStatus
from selfprivacy_api.graphql import schema
import asyncio
import strawberry

# from selfprivacy_api.graphql.schema import Subscription

from selfprivacy_api.jobs.nix_collect_garbage import (
    get_dead_packages,
    nix_collect_garbage,
    parse_line,
    CLEAR_COMPLETED,
    COMPLETED_WITH_ERROR,
    stream_process,
    RESULT_WAS_NOT_FOUND_ERROR,
)


output_print_dead = """
finding garbage collector roots...
determining live/dead paths...
/nix/store/02k8pmw00p7p7mf2dg3n057771w7liia-python3.10-cchardet-2.1.7
/nix/store/03vc6dznx8njbvyd3gfhfa4n5j4lvhbl-python3.10-async-timeout-4.0.2
/nix/store/03ybv2dvfk7c3cpb527y5kzf6i35ch41-python3.10-pycparser-2.21
/nix/store/04dn9slfqwhqisn1j3jv531lms9w5wlj-python3.10-hypothesis-6.50.1.drv
/nix/store/04hhx2z1iyi3b48hxykiw1g03lp46jk7-python-remove-bin-bytecode-hook
"""


output_collect_garbage = """
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


def test_parse_line():
    txt = "190 store paths deleted, 425.51 MiB freed"
    output = (
        JobStatus.FINISHED,
        100,
        CLEAR_COMPLETED,
        "425.51 MiB have been cleared",
    )
    assert parse_line(txt) == output


def test_parse_line_with_blank_line():
    txt = ""
    output = (
        JobStatus.FINISHED,
        100,
        COMPLETED_WITH_ERROR,
        RESULT_WAS_NOT_FOUND_ERROR,
    )
    assert parse_line(txt) == output


def test_get_dead_packages():
    assert get_dead_packages(output_print_dead) == (5, 20.0)


def test_get_dead_packages_zero():
    assert get_dead_packages("") == (0, None)


def test_stream_process():
    log_event = []
    reference = [
        (JobStatus.RUNNING, 20, "Сleaning...", ""),
        (JobStatus.RUNNING, 40, "Сleaning...", ""),
        (JobStatus.RUNNING, 60, "Сleaning...", ""),
        (JobStatus.RUNNING, 80, "Сleaning...", ""),
        (JobStatus.RUNNING, 100, "Сleaning...", ""),
        (
            JobStatus.FINISHED,
            100,
            "Сleaning completed.",
            "425.51 MiB have been cleared",
        ),
    ]

    def set_job_status(status, progress, status_text, result=""):
        log_event.append((status, progress, status_text, result))

    stream_process(output_collect_garbage.split("\n"), 5, set_job_status)
    assert log_event == reference


def test_nix_collect_garbage():
    log_event = []
    reference = [
        (JobStatus.RUNNING, 0, 'Сalculate the number of dead packages...', ''),
        (JobStatus.RUNNING, 0, 'Found 5 packages to remove!', ''),
        (JobStatus.RUNNING, 5, 'Сleaning...', ''),
        (JobStatus.RUNNING, 10, 'Сleaning...', ''),
        (JobStatus.RUNNING, 15, 'Сleaning...', ''),
        (JobStatus.RUNNING, 20, 'Сleaning...', ''),
        (JobStatus.RUNNING, 25, 'Сleaning...', ''),
        (JobStatus.FINISHED, 100, 'Сleaning completed.', '425.51 MiB have been cleared'),
    ]

    def set_job_status(status="", progress="", status_text="", result=""):
        log_event.append((status, progress, status_text, result))

    nix_collect_garbage(
        None,
        None,
        lambda: output_print_dead,
        lambda: output_collect_garbage.split("\n"),
        set_job_status,
    )
    print("log_event:", log_event)
    print("reference:", reference)

    assert log_event == reference


def test_nix_collect_garbage_zero_trash():
    log_event = []
    reference = [
        (JobStatus.RUNNING, 0, "Сalculate the number of dead packages...", ""),
        (JobStatus.FINISHED, 100, "Nothing to clear", "System is clear"),
    ]

    def set_job_status(status="", progress="", status_text="", result=""):
        log_event.append((status, progress, status_text, result))

    nix_collect_garbage(
        None,
        None,
        lambda: "",
        lambda: output_collect_garbage.split("\n"),
        set_job_status,
    )

    assert log_event == reference

# андр констракнш
@pytest.mark.asyncio
async def test_graphql_nix_collect_garbage():
    query = """
    	subscription {
        	nixCollectGarbage()
    	}
    """

    schema_for_garbage = strawberry.Schema(
        query=schema.Query, mutation=schema.Mutation, subscription=schema.Subscription
    )

    sub = await schema_for_garbage.subscribe(query)
    async for result in sub:
        assert not result.errors
        assert result.data == {}
