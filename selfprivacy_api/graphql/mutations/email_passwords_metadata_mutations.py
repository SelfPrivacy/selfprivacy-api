"""Email passwords metadata management module"""

# pylint: disable=too-few-public-methods
from uuid import uuid4
import strawberry

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
)
from selfprivacy_api.actions.email_passwords import (
    add_email_password as action_add_email_password,
    delete_email_password as action_delete_email_password,
)


@strawberry.type
class EmailPasswordMetadataMutations:
    """Mutations change email passwords metadata records"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def add_email_password(
        self,
        username: str,
    ) -> GenericMutationReturn:
        try:
            action_add_email_password(username=username, password_hash=str(uuid4()))
        except Exception as error:
            return GenericMutationReturn(
                success=False,
                message=str(error),  # TODO
                code=409,
            )
        return GenericMutationReturn(
            success=True,
            message="Password added successfully",
            code=201,
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_email_password(self, username: str, uuid: str) -> GenericMutationReturn:
        try:
            action_delete_email_password(username=username, uuid=uuid)
        except Exception as error:
            return GenericMutationReturn(
                success=False,
                message=str(error),  # TODO
                code=409,
            )
        return GenericMutationReturn(
            success=True,
            message="Password deleted successfully",
            code=200,
        )
