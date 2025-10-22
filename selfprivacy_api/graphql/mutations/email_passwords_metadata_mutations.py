"""Email passwords metadata management module"""

import strawberry
from opentelemetry import trace

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
)
from selfprivacy_api.actions.email_passwords import (
    delete_email_password_hash as action_delete_email_password,
)

tracer = trace.get_tracer(__name__)


@strawberry.type
class EmailPasswordsMetadataMutations:
    """Mutations change email passwords metadata records"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_email_password(self, username: str, uuid: str) -> GenericMutationReturn:
        with tracer.start_as_current_span(
            "delete_email_password_mutation",
            attributes={
                "username": username,
                "uuid": uuid,
            },
        ):
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
