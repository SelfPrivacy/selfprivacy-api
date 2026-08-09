from unittest.mock import AsyncMock, call

import pytest

from selfprivacy_api.actions import users
from selfprivacy_api.exceptions import ApiUsingWrongUserRepository
from selfprivacy_api.exceptions.users import (
    DisplaynameTooLong,
    RootUserIsProtected,
    UserNotFound,
)
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin


@pytest.fixture
def users_provider(mocker):
    provider = mocker.Mock()
    provider.create_user = AsyncMock()
    provider.update_user = AsyncMock()
    provider.get_user_by_username = AsyncMock()
    provider.add_users_to_group = AsyncMock()
    provider.remove_users_from_group = AsyncMock()
    mocker.patch.object(users, "ACTIVE_USERS_PROVIDER", provider)
    mocker.patch.object(users.JsonUserRepository, "create_user", new=AsyncMock())
    return provider


@pytest.mark.parametrize(
    "directmemberof",
    [
        [],
        ["sp.full_users"],
        ["sp.admins"],
        ["sp.nextcloud.users"],
        ["sp.nextcloud.admins"],
        ["sp.full_users", "sp.nextcloud.users"],
        ["sp.full_users", "sp.nextcloud.admins"],
        ["sp.admins", "sp.nextcloud.users"],
        ["sp.admins", "sp.nextcloud.admins"],
        ["sp.full_users", "sp.nextcloud.users", "sp.roundcube.admins"],
    ],
)
async def test_create_user_preserves_app_permission_selection(
    users_provider, directmemberof
):
    await users.create_user(username="alice", directmemberof=directmemberof)

    users_provider.create_user.assert_awaited_once_with(
        username="alice",
        directmemberof=directmemberof,
        displayname=None,
        password=None,
    )


async def test_create_user_uses_full_user_default_when_groups_are_omitted(
    users_provider,
):
    await users.create_user(username="alice")

    users_provider.create_user.assert_awaited_once_with(
        username="alice",
        directmemberof=["sp.full_users"],
        displayname=None,
        password=None,
    )


@pytest.mark.parametrize(
    ("current_groups", "requested_groups", "groups_to_add", "groups_to_remove"),
    [
        ([], [], [], []),
        ([], ["sp.full_users"], ["sp.full_users"], []),
        ([], ["sp.admins"], ["sp.admins"], []),
        (["sp.full_users"], [], [], ["sp.full_users"]),
        (["sp.full_users"], ["sp.full_users"], [], []),
        (["sp.full_users"], ["sp.admins"], ["sp.admins"], ["sp.full_users"]),
        (["sp.admins"], [], [], ["sp.admins"]),
        (["sp.admins"], ["sp.full_users"], ["sp.full_users"], ["sp.admins"]),
        (["sp.admins"], ["sp.admins"], [], []),
    ],
)
async def test_update_user_applies_primary_permission_transition(
    users_provider,
    current_groups,
    requested_groups,
    groups_to_add,
    groups_to_remove,
):
    users_provider.get_user_by_username.return_value = UserDataUser(
        username="alice",
        user_type=UserDataUserOrigin.NORMAL,
        directmemberof=current_groups,
    )

    await users.update_user(username="alice", directmemberof=requested_groups)

    assert users_provider.add_users_to_group.await_args_list == [
        call(group_name=group, users=["alice"]) for group in groups_to_add
    ]
    assert users_provider.remove_users_from_group.await_args_list == [
        call(group_name=group, users=["alice"]) for group in groups_to_remove
    ]


@pytest.mark.parametrize(
    ("current_groups", "requested_groups", "groups_to_add", "groups_to_remove"),
    [
        ([], ["sp.nextcloud.users"], ["sp.nextcloud.users"], []),
        (["sp.nextcloud.users"], [], [], ["sp.nextcloud.users"]),
        ([], ["sp.nextcloud.admins"], ["sp.nextcloud.admins"], []),
        (["sp.nextcloud.admins"], [], [], ["sp.nextcloud.admins"]),
        (
            ["sp.full_users", "sp.nextcloud.users"],
            ["sp.admins", "sp.nextcloud.users"],
            ["sp.admins"],
            ["sp.full_users"],
        ),
        (
            ["sp.full_users", "sp.nextcloud.users"],
            ["sp.full_users", "sp.roundcube.admins"],
            ["sp.roundcube.admins"],
            ["sp.nextcloud.users"],
        ),
        (
            ["sp.full_users", "sp.example.unknown"],
            ["sp.admins", "sp.example.unknown"],
            ["sp.admins"],
            ["sp.full_users"],
        ),
    ],
)
async def test_update_user_applies_explicit_permission_transition(
    users_provider,
    current_groups,
    requested_groups,
    groups_to_add,
    groups_to_remove,
):
    users_provider.get_user_by_username.return_value = UserDataUser(
        username="alice",
        user_type=UserDataUserOrigin.NORMAL,
        directmemberof=current_groups,
    )

    await users.update_user(username="alice", directmemberof=requested_groups)

    assert users_provider.add_users_to_group.await_args_list == [
        call(group_name=group, users=["alice"]) for group in groups_to_add
    ]
    assert users_provider.remove_users_from_group.await_args_list == [
        call(group_name=group, users=["alice"]) for group in groups_to_remove
    ]


async def test_update_user_keeps_groups_when_they_are_omitted(users_provider):
    await users.update_user(username="alice")

    users_provider.get_user_by_username.assert_not_awaited()
    users_provider.add_users_to_group.assert_not_awaited()
    users_provider.remove_users_from_group.assert_not_awaited()


async def test_update_user_updates_legacy_email_password(users_provider, mocker):
    update_password = mocker.patch.object(users, "update_legacy_email_password_hash")

    await users.update_user(username="alice", password="new password")

    update_password.assert_called_once_with(
        username="alice",
        password="new password",
        with_created_at=True,
    )


@pytest.mark.parametrize("password", [None, ""])
async def test_update_user_ignores_empty_password(users_provider, mocker, password):
    update_password = mocker.patch.object(users, "update_legacy_email_password_hash")

    await users.update_user(username="alice", password=password)

    update_password.assert_not_called()


async def test_update_user_rejects_root_before_writes(users_provider, mocker):
    update_password = mocker.patch.object(users, "update_legacy_email_password_hash")

    with pytest.raises(RootUserIsProtected):
        await users.update_user(
            username="root",
            password="new password",
            displayname="Root",
            directmemberof=[],
        )

    update_password.assert_not_called()
    users_provider.update_user.assert_not_awaited()
    users_provider.get_user_by_username.assert_not_awaited()
    users_provider.add_users_to_group.assert_not_awaited()
    users_provider.remove_users_from_group.assert_not_awaited()


@pytest.mark.parametrize("displayname", ["Alice", "a" * 254])
async def test_update_user_updates_valid_displayname(users_provider, displayname):
    await users.update_user(username="alice", displayname=displayname)

    users_provider.update_user.assert_awaited_once_with(
        username="alice", displayname=displayname
    )


async def test_update_user_ignores_empty_displayname(users_provider):
    await users.update_user(username="alice", displayname="")

    users_provider.update_user.assert_not_awaited()


async def test_update_user_rejects_long_displayname_before_writes(
    users_provider, mocker
):
    update_password = mocker.patch.object(users, "update_legacy_email_password_hash")

    with pytest.raises(DisplaynameTooLong):
        await users.update_user(
            username="alice",
            password="new password",
            displayname="a" * 255,
        )

    update_password.assert_not_called()
    users_provider.update_user.assert_not_awaited()


@pytest.mark.parametrize(
    "user_changes",
    [
        {"displayname": "Alice"},
        {"directmemberof": []},
    ],
)
async def test_update_user_rejects_unsupported_json_repository_before_writes(
    mocker, user_changes
):
    mocker.patch.object(users, "ACTIVE_USERS_PROVIDER", users.JsonUserRepository)
    update_password = mocker.patch.object(users, "update_legacy_email_password_hash")

    with pytest.raises(ApiUsingWrongUserRepository):
        await users.update_user(
            username="alice",
            password="new password",
            **user_changes,
        )

    update_password.assert_not_called()


async def test_update_user_does_not_modify_default_groups(users_provider):
    users_provider.get_user_by_username.return_value = UserDataUser(
        username="alice",
        user_type=UserDataUserOrigin.NORMAL,
        directmemberof=["idm_people_self_name_write", "sp.nextcloud.users"],
    )

    await users.update_user(
        username="alice",
        directmemberof=["idm_all_persons", "sp.admins"],
    )

    users_provider.add_users_to_group.assert_awaited_once_with(
        group_name="sp.admins", users=["alice"]
    )
    users_provider.remove_users_from_group.assert_awaited_once_with(
        group_name="sp.nextcloud.users", users=["alice"]
    )


async def test_update_user_applies_all_valid_changes(users_provider, mocker):
    update_password = mocker.patch.object(users, "update_legacy_email_password_hash")
    users_provider.get_user_by_username.return_value = UserDataUser(
        username="alice",
        user_type=UserDataUserOrigin.NORMAL,
        directmemberof=["sp.full_users"],
    )

    await users.update_user(
        username="alice",
        password="new password",
        displayname="Alice",
        directmemberof=["sp.admins"],
    )

    update_password.assert_called_once_with(
        username="alice",
        password="new password",
        with_created_at=True,
    )
    users_provider.update_user.assert_awaited_once_with(
        username="alice", displayname="Alice"
    )
    users_provider.add_users_to_group.assert_awaited_once_with(
        group_name="sp.admins", users=["alice"]
    )
    users_provider.remove_users_from_group.assert_awaited_once_with(
        group_name="sp.full_users", users=["alice"]
    )


async def test_update_user_prepares_group_changes_before_writes(users_provider, mocker):
    update_password = mocker.patch.object(users, "update_legacy_email_password_hash")
    users_provider.get_user_by_username.side_effect = UserNotFound

    with pytest.raises(UserNotFound):
        await users.update_user(
            username="alice",
            password="new password",
            displayname="Alice",
            directmemberof=["sp.admins"],
        )

    update_password.assert_not_called()
    users_provider.update_user.assert_not_awaited()
    users_provider.add_users_to_group.assert_not_awaited()
    users_provider.remove_users_from_group.assert_not_awaited()
