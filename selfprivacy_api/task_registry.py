from os import environ

from selfprivacy_api.utils.huey import huey

from selfprivacy_api.backup.tasks import *
from selfprivacy_api.services.tasks import move_service
from selfprivacy_api.jobs.upgrade_system import rebuild_system_task

from selfprivacy_api.jobs.test import test_job
from selfprivacy_api.jobs.nix_collect_garbage import calculate_and_clear_dead_paths


if environ.get("TEST_MODE"):
    from tests.test_huey import sum
