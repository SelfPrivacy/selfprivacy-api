import gettext

from selfprivacy_api.exceptions.kanidm import KanidmQueryError
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType
from selfprivacy_api.utils.kanidm import (
    check_kanidm_response_type,
    send_kanidm_query,
)

_ = gettext.gettext


FAILED_TO_KANIDM_GET_MINIMUM_CREDENTIAL_TYPE = _(
    'Error while trying to get the Kanidm minimum credential type: Kanidm did not return a valid "credential_type_minimum" value for the group idm_all_persons.'
)


async def get_kanidm_minimum_credential_type() -> KanidmCredentialType:
    endpoint = "group/idm_all_persons/_attr/credential_type_minimum"
    method = "GET"

    credential_type_data = await send_kanidm_query(
        endpoint=endpoint,
        method=method,
    )

    check_kanidm_response_type(
        endpoint=endpoint,
        method=method,
        data_type="list",
        response_data=credential_type_data,
    )

    try:
        return KanidmCredentialType(credential_type_data[0])
    except (IndexError, ValueError) as error:
        raise KanidmQueryError(
            endpoint=endpoint,
            method=method,
            description=FAILED_TO_KANIDM_GET_MINIMUM_CREDENTIAL_TYPE,
            error_text=error,
        )


async def set_kanidm_minimum_credential_type(
    minimum_credential_type: KanidmCredentialType,
) -> None:
    endpoint = "group/idm_all_persons/_attr/credential_type_minimum"
    method = "PUT"

    await send_kanidm_query(
        endpoint=endpoint,
        method=method,
        data=[minimum_credential_type.value],
    )
