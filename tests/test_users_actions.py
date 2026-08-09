from unittest.mock import AsyncMock, call

import pytest

from selfprivacy_api.actions import users
from selfprivacy_api.models.user import UserDataUser, UserDataUserOrigin


@pytest.fixture
def users_provider(mocker):
    provider = mocker.Mock()
    provider.create_user = AsyncMock()
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
