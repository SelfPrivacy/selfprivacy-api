# pylint: disable=too-few-public-methods
import strawberry

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.kanidm_credential_type import (
    KanidmCredentialTypeEnum,
    KanidmCredentialTypeMutationReturn,
)
from selfprivacy_api.actions.kanidm_credential_type import (
    InvalidKanidmCredentialType,
    set_kanidm_minimum_credential_type as set_kanidm_minimum_credential_type_action,
    get_kanidm_minimum_credential_type as get_kanidm_minimum_credential_type_action,
)
from selfprivacy_api.models.kanidm_credential_type import (
    KanidmCredentialType as ModelKanidmCredentialType,
)


@strawberry.input
class SetKanidmMinimumCredentialTypeInput:
    """Input type for set_kanidm_minimum_credential_type mutation"""

    minimum_credential_type: KanidmCredentialTypeEnum


@strawberry.type
class KanidmMutations:
    """Mutations change Kanidm settings"""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def set_kanidm_minimum_credential_type(
        self, minimum_credential_type: SetKanidmMinimumCredentialTypeInput
    ) -> KanidmCredentialTypeMutationReturn:
        try:
            set_kanidm_minimum_credential_type_action(
                minimum_credential_type=ModelKanidmCredentialType(
                    minimum_credential_type.minimum_credential_type.value
                )
            )
        except InvalidKanidmCredentialType as error:
            return KanidmCredentialTypeMutationReturn(
                success=False,
                message=error.get_error_message(),
                code=409,
            )

        return KanidmCredentialTypeMutationReturn(
            success=True,
            message="Success",
            code=200,
            minimum_credential_type=get_kanidm_minimum_credential_type_action().minimum_credential_type,
        )
