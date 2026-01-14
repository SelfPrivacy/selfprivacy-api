# pylint: disable=too-few-public-methods
import strawberry
from strawberry.types import Info

from selfprivacy_api.actions.kanidm_credential_type import (
    set_kanidm_minimum_credential_type as set_kanidm_minimum_credential_type_action,
)
from selfprivacy_api.exceptions.abstract_exception import AbstractException
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.kanidm_credential_type import (
    KanidmCredentialTypeEnum,
    KanidmCredentialTypeMutationReturn,
)
from selfprivacy_api.models.kanidm_credential_type import (
    KanidmCredentialType as ModelKanidmCredentialType,
)
from selfprivacy_api.utils.localization import get_locale


@strawberry.input
class SetKanidmMinimumCredentialTypeInput:
    """Input type for set_kanidm_minimum_credential_type mutation"""

    minimum_credential_type: KanidmCredentialTypeEnum


@strawberry.type
class KanidmMutations:
    """Mutations change Kanidm settings"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def set_kanidm_minimum_credential_type(
        self, minimum_credential_type: SetKanidmMinimumCredentialTypeInput, info: Info
    ) -> KanidmCredentialTypeMutationReturn:
        locale = get_locale(info=info)

        try:
            await set_kanidm_minimum_credential_type_action(
                minimum_credential_type=ModelKanidmCredentialType(
                    minimum_credential_type.minimum_credential_type.value
                )
            )
        except Exception as error:
            if isinstance(error, AbstractException):
                return KanidmCredentialTypeMutationReturn(
                    success=False,
                    message=error.get_error_message(locale=locale),
                    code=error.code,
                )
            else:
                return KanidmCredentialTypeMutationReturn(
                    success=False,
                    message=str(error),
                    code=400,
                )

        return KanidmCredentialTypeMutationReturn(
            success=True,
            message="Success",
            code=200,
            minimum_credential_type=minimum_credential_type.minimum_credential_type,
        )
