# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import pytest

from selfprivacy_api.jobs.nix_collect_garbage import nix_collect_garbage





    created_at: datetime.datetime
    updated_at: datetime.datetime
    uid: UUID
    type_id: str
    name: str
    description: str
    status: JobStatus


def test_nix_collect_garbage(job(
    created_at = "2019-12-04",
    updated_at = "2019-12-04",
    uid = UUID,
    type_id = "typeid",
    name = "name",
    description: "desc",
    status = status(CREATED = "CREATED"),
)):

    assert nix_collect_garbage() is not None
