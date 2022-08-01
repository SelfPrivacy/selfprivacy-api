#!/usr/bin/env python3
"""Users management module"""
# pylint: disable=too-few-public-methods

import strawberry

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.ssh_utils import (
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

        success, message, code = create_ssh_key(ssh_input.username, ssh_input.ssh_key)

        return UserMutationReturn(
            success=success,
            message=message,
            code=code,
            user=get_user_by_username(ssh_input.username),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def remove_ssh_key(self, ssh_input: SshMutationInput) -> UserMutationReturn:
        """Remove ssh key from user"""

        success, message, code = remove_ssh_key(ssh_input.username, ssh_input.ssh_key)

        return UserMutationReturn(
            success=success,
            message=message,
            code=code,
            user=get_user_by_username(ssh_input.username),
        )
