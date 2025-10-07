"""Email passwords metadata management module"""

import gettext

import strawberry
from strawberry.types import Info

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
)
from selfprivacy_api.actions.email_passwords import (
    delete_email_password_hash as action_delete_email_password,
)
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

_ = gettext.gettext


@strawberry.type
class EmailPasswordsMetadataMutations:
    """Mutations change email passwords metadata records"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete_email_password(
        self, username: str, uuid: str, info: Info
    ) -> GenericMutationReturn:

        locale = info.context["locale"]
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
            message=t.translate(text=_("Password deleted successfully"), locale=locale),
            code=200,
        )
