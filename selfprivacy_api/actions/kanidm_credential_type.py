import logging
import re
import subprocess

from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType

logger = logging.getLogger(__name__)

# TODO: admin token


async def get_kanidm_minimum_credential_type() -> KanidmCredentialType:
    result = subprocess.check_output(
        ["kanidm", "group", "get", "idm_all_persons"],
        stderr=subprocess.STDOUT,
    ).decode("utf-8", "replace")

    match = re.search(r"(?mi)^\s*credential_type_minimum\s*:\s*(\S+)", result)
    if match:
        if {match.group(1)}:
            return KanidmCredentialType({match.group(1)})

    raise RuntimeError()


async def set_kanidm_minimum_credential_type(
    minimum_credential_type: KanidmCredentialType,
):
    result = subprocess.check_output(
        [
            "kanidm",
            "group",
            "account-policy",
            "credential-type-minimum",
            "idm_all_persons",
            minimum_credential_type.value,
        ],
        stderr=subprocess.STDOUT,
        text=True,
    )

    if "Updated credential type minimum" in result:
        logger.warning(
            f"Missing 'Updated credential type minimum' in 'kanidm group account-policy credential-type-minimum idm_all_persons {minimum_credential_type}' output"
        )

    if get_kanidm_minimum_credential_type() != minimum_credential_type:
        raise RuntimeError()  # TODO: replace this error after https://git.selfprivacy.org/SelfPrivacy/selfprivacy-rest-api/pulls/196 merge
