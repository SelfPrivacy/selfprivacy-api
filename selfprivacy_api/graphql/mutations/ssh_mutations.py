#!/usr/bin/env python3
"""Users management module"""
# pylint: disable=too-few-public-methods

import strawberry
from selfprivacy_api.actions.users import UserNotFound

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.actions.ssh import (
    InvalidPublicKey,
    KeyAlreadyExists,
    KeyNotFound,
    create_ssh_key,
    remove_ssh_key,
)
from selfprivacy_api.graphql.common_types.user import (
    UserMutationReturn,
    get_user_by_username,
)


@strawberry.input
class SshMutationInput:
    """Input type for ssh mutation"""

    username: str
    ssh_key: str


@strawberry.type
class SshMutations:
    """Mutations ssh"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def add_ssh_key(self, ssh_input: SshMutationInput) -> UserMutationReturn:
        """Add a new ssh key"""

        try:
            create_ssh_key(ssh_input.username, ssh_input.ssh_key)
        except KeyAlreadyExists:
            return UserMutationReturn(
                success=False,
                message="Key already exists",
                code=409,
            )
        except InvalidPublicKey:
            return UserMutationReturn(
                success=False,
                message="Invalid key type. Only ssh-ed25519 and ssh-rsa are supported",
                code=400,
            )
        except UserNotFound:
            return UserMutationReturn(
                success=False,
                message="User not found",
                code=404,
            )
        except Exception as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

        return UserMutationReturn(
            success=True,
            message="New SSH key successfully written",
            code=201,
            user=get_user_by_username(ssh_input.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_ssh_key(self, ssh_input: SshMutationInput) -> UserMutationReturn:
        """Remove ssh key from user"""

        try:
            remove_ssh_key(ssh_input.username, ssh_input.ssh_key)
        except KeyNotFound:
            return UserMutationReturn(
                success=False,
                message="Key not found",
                code=404,
            )
        except UserNotFound:
            return UserMutationReturn(
                success=False,
                message="User not found",
                code=404,
            )
        except Exception as e:
            return UserMutationReturn(
                success=False,
                message=str(e),
                code=500,
            )

        return UserMutationReturn(
            success=True,
            message="SSH key successfully removed",
            code=200,
            user=get_user_by_username(ssh_input.username),
        )
