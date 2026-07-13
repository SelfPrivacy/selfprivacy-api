# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import json

import httpx
import pytest

from selfprivacy_api.exceptions.users.kanidm_repository import KanidmQueryError
from selfprivacy_api.migrations.migrate_users_from_json import MigrateUsersFromJson
from selfprivacy_api.utils import WriteUserData
from selfprivacy_api.utils.redis_pool import RedisPool

from tests.test_migrations.conftest import ALL_USERS, PRIMARY_USER


@pytest.fixture
def clean_email_passwords():
    """Remove email password hashes of turned_on.json users from the real
    Redis before and after the test to avoid crosstalk."""
    redis = RedisPool().get_userpanel_connection()

    def clean():
        for username in ALL_USERS:
            for key in redis.scan_iter(f"priv/user/{username}/passwords/*"):
                redis.delete(key)

    clean()
    yield redis
    clean()


ZERO_UUID = "00000000-0000-0000-0000-000000000000"

# Hashes of the users in tests/data/turned_on.json
PASSWORD_HASHES = {
    "tester": "HASHED_PASSWORD",
    "user1": "HASHED_PASSWORD_1",
    "user2": "HASHED_PASSWORD_2",
    "user3": "HASHED_PASSWORD_3",
}

KANIDM_URL = "https://auth.test.tld"


def kanidm_person(name: str) -> dict:
    """A person entry shaped like a real Kanidm GET /v1/person response
    (see tests/test_repository/test_kanidm_user_repository.py)."""
    groups = ["sp.full_users@test.tld"]
    if name == PRIMARY_USER:
        groups = ["sp.admins@test.tld"] + groups
    return {
        "attrs": {
            "class": ["account", "memberof", "object", "person"],
            "name": [name],
            "spn": [f"{name}@test.tld"],
            "uuid": ["9cb45c33-c332-4e60-9b14-691f55ad1c21"],
            "displayname": [name],
            "mail": [f"{name}@test.tld"],
            "memberof": groups + ["idm_all_persons@test.tld"],
            "directmemberof": groups,
        }
    }


@pytest.fixture
def kanidm_boundary(generic_userdata, kanidm_api, mock_kanidm_domain, mock_admin_token):
    return kanidm_api


def script_user_creation(kanidm_api, usernames):
    """Script one POST /v1/person + one group POST per user."""
    for _ in usernames:
        kanidm_api.respond(200, None)  # create person
        kanidm_api.respond(200, None)  # add to group


def assert_user_creation_requests(requests, username):
    """Assert a (create person, add to group) request pair for username."""
    create, group = requests
    assert create.method == "POST"
    assert str(create.url) == f"{KANIDM_URL}/v1/person"
    assert json.loads(create.content) == {
        "attrs": {
            "name": [username],
            "displayname": [username],
            "mail": [f"{username}@test.tld"],
            "class": ["user"],
        }
    }

    expected_group = "sp.admins" if username == PRIMARY_USER else "sp.full_users"
    assert group.method == "POST"
    assert str(group.url) == f"{KANIDM_URL}/v1/group/{expected_group}/_attr/member"
    assert json.loads(group.content) == [username]


def stored_password_hash(redis, username):
    return redis.hgetall(f"priv/user/{username}/passwords/{ZERO_UUID}").get("password")


async def test_needed_when_json_user_missing_in_kanidm(kanidm_boundary):
    kanidm_boundary.respond(200, [kanidm_person("user1")])

    assert await MigrateUsersFromJson().is_migration_needed() is True

    assert len(kanidm_boundary.requests) == 1
    request = kanidm_boundary.requests[0]
    assert request.method == "GET"
    assert str(request.url) == f"{KANIDM_URL}/v1/person"


async def test_not_needed_when_all_users_in_kanidm(kanidm_boundary):
    kanidm_boundary.respond(200, [kanidm_person(name) for name in ALL_USERS])

    assert await MigrateUsersFromJson().is_migration_needed() is False


async def test_migrate_creates_users_and_stores_hashes(
    kanidm_boundary, clean_email_passwords
):
    redis = clean_email_passwords
    kanidm_boundary.respond(200, [])  # GET person inside migrate()
    # JsonUserRepository returns normal users first, the primary user last
    script_user_creation(kanidm_boundary, ALL_USERS)

    await MigrateUsersFromJson().migrate()

    requests = kanidm_boundary.requests
    assert len(requests) == 1 + 2 * len(ALL_USERS)
    for position, username in enumerate(ALL_USERS):
        assert_user_creation_requests(
            requests[1 + 2 * position : 3 + 2 * position], username
        )

    for username in ALL_USERS:
        assert stored_password_hash(redis, username) == PASSWORD_HASHES[username]


async def test_migrate_isolates_per_user_failure(
    kanidm_boundary, clean_email_passwords
):
    redis = clean_email_passwords
    kanidm_boundary.respond(200, [])  # GET person inside migrate()
    # First user fails to be created in Kanidm...
    kanidm_boundary.respond(500, {"error": "internal"})
    # ...the rest succeed
    script_user_creation(kanidm_boundary, ["user2", "user3", PRIMARY_USER])

    await MigrateUsersFromJson().migrate()

    requests = kanidm_boundary.requests
    # user1: only the failed person POST, no group request
    assert len(requests) == 1 + 1 + 2 * 3
    group_bodies = [
        json.loads(request.content)
        for request in requests
        if "/_attr/member" in str(request.url)
    ]
    assert ["user1"] not in group_bodies

    # No password stored for the failed user, all stored for the others
    assert stored_password_hash(redis, "user1") is None
    for username in ["user2", "user3", PRIMARY_USER]:
        assert stored_password_hash(redis, username) == PASSWORD_HASHES[username]


async def test_migrate_skips_hash_write_for_user_without_password(
    kanidm_boundary, clean_email_passwords
):
    redis = clean_email_passwords
    with WriteUserData() as data:
        for user in data["users"]:
            if user["username"] == "user3":
                del user["hashedPassword"]

    kanidm_boundary.respond(200, [])  # GET person inside migrate()
    script_user_creation(kanidm_boundary, ALL_USERS)

    await MigrateUsersFromJson().migrate()

    # user3 was still created in Kanidm...
    assert len(kanidm_boundary.requests) == 1 + 2 * len(ALL_USERS)
    # ...but no password hash was written for it
    assert stored_password_hash(redis, "user3") is None
    for username in ["user1", "user2", PRIMARY_USER]:
        assert stored_password_hash(redis, username) == PASSWORD_HASHES[username]


async def test_is_migration_needed_propagates_kanidm_outage(kanidm_boundary):
    # The blanket except in run_migrations() is what protects API startup
    # from this error, not the migration itself.
    kanidm_boundary.fail(httpx.ConnectError("Connection refused"))

    with pytest.raises(KanidmQueryError):
        await MigrateUsersFromJson().is_migration_needed()
