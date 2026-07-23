# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

import json

import pytest

from selfprivacy_api.exceptions.kanidm import (
    KanidmReturnEmptyResponse,
    KanidmReturnUnknownResponseType,
    NoPasswordResetLinkFoundInResponse,
)
from selfprivacy_api.exceptions.users import (
    UserAlreadyExists,
    UserNotFound,
    UserOrGroupNotFound,
)
from selfprivacy_api.models.user import UserDataUserOrigin
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)

# Shapes verified against a live Kanidm server on 2026-07-07
KANIDM_USERS_RESPONSE = [
    {
        "attrs": {
            "class": ["account", "memberof", "object", "person"],
            "name": ["admin_user"],
            "spn": ["admin_user@test.tld"],
            "uuid": ["2b0da2fd-bc36-433a-9ce0-6ca5303c6a9d"],
            "displayname": ["Admin User"],
            "mail": ["admin_user@test.tld"],
            "memberof": [
                "sp.admins@test.tld",
                "sp.full_users@test.tld",
                "idm_all_persons@test.tld",
                "idm_all_accounts@test.tld",
                "idm_people_self_name_write@test.tld",
            ],
            "directmemberof": [
                "sp.admins@test.tld",
                "idm_all_persons@test.tld",
            ],
            "passkeys": ["main key"],
        }
    },
    {
        "attrs": {
            "class": ["account", "memberof", "object", "person"],
            "name": ["alice"],
            "spn": ["alice@test.tld"],
            "uuid": ["9cb45c33-c332-4e60-9b14-691f55ad1c21"],
            "displayname": ["Alice"],
            "mail": ["alice@test.tld"],
            "memberof": [
                "sp.full_users@test.tld",
                "idm_all_persons@test.tld",
                "idm_all_accounts@test.tld",
            ],
            "directmemberof": ["sp.full_users@test.tld"],
        }
    },
]

KANIDM_GROUPS_RESPONSE = [
    # skipped: builtin class
    {
        "attrs": {
            "name": ["idm_admins"],
            "class": ["builtin", "group", "object"],
        }
    },
    # skipped: blocklisted name
    {
        "attrs": {
            "name": ["ext_idm_provisioned_entities"],
            "class": ["group", "object"],
        }
    },
    {
        "attrs": {
            "name": ["sp.admins"],
            "class": ["group", "memberof", "object"],
            "member": ["alice@test.tld", "bob@test.tld"],
            "memberof": ["sp.full_users@test.tld"],
            "directmemberof": ["sp.full_users@test.tld"],
            "spn": ["sp.admins@test.tld"],
            "uuid": ["7a1f1e2d-0b52-4c1e-9f3a-1d2e3f4a5b6c"],
        }
    },
    # user-created groups may carry a description
    {
        "attrs": {
            "name": ["book.club"],
            "class": ["group", "object"],
            "spn": ["book.club@test.tld"],
            "uuid": ["3c9d8e7f-6a5b-4c3d-2e1f-0a9b8c7d6e5f"],
            "description": ["We read books"],
        }
    },
]


# --- Static helpers -----------------------------------------------------------


def test_check_user_origin_by_memberof():
    assert (
        KanidmUserRepository._check_user_origin_by_memberof(
            memberof=["sp.admins", "sp.full_users"]
        )
        == UserDataUserOrigin.PRIMARY
    )
    assert (
        KanidmUserRepository._check_user_origin_by_memberof(memberof=["sp.full_users"])
        == UserDataUserOrigin.NORMAL
    )


# --- create_user --------------------------------------------------------------


async def test_create_user_sends_expected_request(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    await KanidmUserRepository.create_user(username="alice")

    assert len(kanidm_api.requests) == 1
    request = kanidm_api.requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://auth.test.tld/v1/person"
    assert json.loads(request.content) == {
        "attrs": {
            "name": ["alice"],
            "displayname": ["alice"],  # defaults to the username
            "mail": ["alice@test.tld"],
            "class": ["user"],
        }
    }


async def test_create_user_with_displayname_and_groups(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)
    kanidm_api.respond(200, None)
    kanidm_api.respond(200, None)

    await KanidmUserRepository.create_user(
        username="alice",
        displayname="Alice A.",
        directmemberof=["group1", "group2"],
    )

    assert len(kanidm_api.requests) == 3
    person_request, group1_request, group2_request = kanidm_api.requests

    assert json.loads(person_request.content)["attrs"]["displayname"] == ["Alice A."]

    assert group1_request.method == "POST"
    assert (
        str(group1_request.url) == "https://auth.test.tld/v1/group/group1/_attr/member"
    )
    assert json.loads(group1_request.content) == ["alice"]

    assert group2_request.method == "POST"
    assert (
        str(group2_request.url) == "https://auth.test.tld/v1/group/group2/_attr/member"
    )
    assert json.loads(group2_request.content) == ["alice"]


# --- get_users ----------------------------------------------------------------


async def test_get_users_parses_users_and_strips_default_groups(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, KANIDM_USERS_RESPONSE)

    users = await KanidmUserRepository.get_users()

    request = kanidm_api.requests[0]
    assert request.method == "GET"
    assert str(request.url) == "https://auth.test.tld/v1/person"

    assert len(users) == 2
    admin, alice = users

    assert admin.username == "admin_user"
    assert admin.user_type == UserDataUserOrigin.PRIMARY
    assert admin.memberof == ["sp.admins", "sp.full_users"]
    assert admin.directmemberof == ["sp.admins"]
    assert admin.display_name == "Admin User"
    assert admin.email == "admin_user@test.tld"
    assert admin.ssh_keys == []

    assert alice.username == "alice"
    assert alice.user_type == UserDataUserOrigin.NORMAL
    assert alice.memberof == ["sp.full_users"]
    assert alice.directmemberof == ["sp.full_users"]
    assert alice.display_name == "Alice"
    assert alice.email == "alice@test.tld"


async def test_get_users_exclude_primary(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, KANIDM_USERS_RESPONSE)

    users = await KanidmUserRepository.get_users(exclude_primary=True)

    assert [user.username for user in users] == ["alice"]


async def test_get_users_exclude_root_is_a_noop(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    # Current behavior: exclude_root does nothing for Kanidm (there is no
    # root filtering in the code at all; Kanidm just never returns root).
    kanidm_api.respond(200, KANIDM_USERS_RESPONSE)
    kanidm_api.respond(200, KANIDM_USERS_RESPONSE)

    default_users = await KanidmUserRepository.get_users()
    users_without_root = await KanidmUserRepository.get_users(exclude_root=True)

    assert default_users == users_without_root


async def test_get_users_unexpected_response_type_raises(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, {"attrs": {}})

    with pytest.raises(KanidmReturnUnknownResponseType):
        await KanidmUserRepository.get_users()


async def test_get_users_empty_response_raises(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    with pytest.raises(KanidmReturnEmptyResponse):
        await KanidmUserRepository.get_users()


# --- get_user_by_username -----------------------------------------------------


async def test_get_user_by_username_success(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, KANIDM_USERS_RESPONSE[1])

    user = await KanidmUserRepository.get_user_by_username("alice")

    request = kanidm_api.requests[0]
    assert request.method == "GET"
    assert str(request.url) == "https://auth.test.tld/v1/person/alice"

    assert user.username == "alice"
    assert user.user_type == UserDataUserOrigin.NORMAL
    assert user.memberof == ["sp.full_users"]
    assert user.directmemberof == ["sp.full_users"]
    assert user.display_name == "Alice"
    assert user.email == "alice@test.tld"
    assert user.ssh_keys == []


async def test_get_user_by_username_empty_response_raises_user_not_found(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    with pytest.raises(UserNotFound):
        await KanidmUserRepository.get_user_by_username("ghost")


async def test_get_user_by_username_wrong_type_raises(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, ["not", "a", "dict"])

    with pytest.raises(KanidmReturnUnknownResponseType):
        await KanidmUserRepository.get_user_by_username("alice")


# --- delete_user / update_user ------------------------------------------------


async def test_delete_user_sends_delete_request(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    await KanidmUserRepository.delete_user("alice")

    request = kanidm_api.requests[0]
    assert request.method == "DELETE"
    assert str(request.url) == "https://auth.test.tld/v1/person/alice"
    assert request.content == b""


async def test_update_user_with_displayname(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    await KanidmUserRepository.update_user(username="alice", displayname="Alice B.")

    request = kanidm_api.requests[0]
    assert request.method == "PATCH"
    assert str(request.url) == "https://auth.test.tld/v1/person/alice"
    assert json.loads(request.content) == {
        "attrs": {
            "mail": ["alice@test.tld"],
            "displayname": ["Alice B."],
        }
    }


async def test_update_user_without_displayname_only_updates_mail(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    await KanidmUserRepository.update_user(username="alice")

    request = kanidm_api.requests[0]
    assert json.loads(request.content) == {
        "attrs": {
            "mail": ["alice@test.tld"],
        }
    }


# --- generate_password_reset_link ----------------------------------------------


async def test_generate_password_reset_link_success(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, {"token": "abc123", "expiry_time": 1234567890})

    link = await KanidmUserRepository.generate_password_reset_link("alice")

    request = kanidm_api.requests[0]
    assert request.method == "GET"
    assert (
        str(request.url)
        == "https://auth.test.tld/v1/person/alice/_credential/_update_intent"
    )
    assert link == "https://auth.test.tld/ui/reset?token=abc123"


async def test_generate_password_reset_link_missing_token_raises(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, {"expiry_time": 1234567890})

    with pytest.raises(NoPasswordResetLinkFoundInResponse):
        await KanidmUserRepository.generate_password_reset_link("alice")


async def test_generate_password_reset_link_empty_response_raises(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    with pytest.raises(KanidmReturnEmptyResponse):
        await KanidmUserRepository.generate_password_reset_link("alice")


# --- get_groups -----------------------------------------------------------------


async def test_get_groups_parses_and_filters_builtin_groups(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, KANIDM_GROUPS_RESPONSE)

    groups = await KanidmUserRepository.get_groups()

    request = kanidm_api.requests[0]
    assert request.method == "GET"
    assert str(request.url) == "https://auth.test.tld/v1/group"

    assert len(groups) == 2
    group = groups[0]
    assert group.name == "sp.admins"
    assert group.group_class == ["group", "memberof", "object"]
    assert group.member == ["alice", "bob"]
    assert group.memberof == ["sp.full_users"]
    assert group.directmemberof == ["sp.full_users"]
    assert group.spn == "sp.admins@test.tld"
    assert group.description is None

    described = groups[1]
    assert described.name == "book.club"
    assert described.description == "We read books"


async def test_get_groups_empty_response_raises(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    with pytest.raises(KanidmReturnEmptyResponse):
        await KanidmUserRepository.get_groups()


# --- group membership -----------------------------------------------------------


async def test_add_users_to_group_sends_expected_request(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    await KanidmUserRepository.add_users_to_group(
        users=["alice", "bob"], group_name="sp.admins"
    )

    request = kanidm_api.requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://auth.test.tld/v1/group/sp.admins/_attr/member"
    assert json.loads(request.content) == ["alice", "bob"]


async def test_remove_users_from_group_sends_expected_request(
    kanidm_api, mock_kanidm_domain, mock_admin_token
):
    kanidm_api.respond(200, None)

    await KanidmUserRepository.remove_users_from_group(
        users=["alice"], group_name="sp.admins"
    )

    request = kanidm_api.requests[0]
    assert request.method == "DELETE"
    assert str(request.url) == "https://auth.test.tld/v1/group/sp.admins/_attr/member"
    assert json.loads(request.content) == ["alice"]
