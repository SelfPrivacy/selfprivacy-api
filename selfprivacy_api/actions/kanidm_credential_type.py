import logging

from selfprivacy_api.utils import ReadUserData, WriteUserData

from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType


logger = logging.getLogger(__name__)


DEFAULT_KANIDM_MINIMUM_CREDENTIAL_TYPE = KanidmCredentialType.mfa


class InvalidKanidmCredentialType(Exception):
    """Invalid Kanidm Credential Type"""

    @staticmethod
    def get_error_message() -> str:
        return """
        Invalid value 'minimum_credential_type'
        for enum 'KanidmCredentialLvl' in /etc/nixos/userdata.json.
        Support only 'any', 'mfa', 'passkey'.
        See https://kanidm.github.io/kanidm/stable/accounts/account_policy.html
        """


def get_kanidm_minimum_credential_type() -> KanidmCredentialType:
    with ReadUserData() as data:
        if "kanidm" in data:
            if "minimum_credential_type" in data["kanidm"]:
                raw = data["minimum_credential_type"]
                try:
                    return KanidmCredentialType(str(raw))
                except ValueError:
                    raise InvalidKanidmCredentialType(f"Unsupported level: {raw}")

        logger.warning(
            """
            Missing 'kanidm/minimum_credential_type' key in /etc/nixos/userdata.json.
            Setting the default value.
            """
        )
        set_kanidm_minimum_credential_type(
            minimum_credential_type=DEFAULT_KANIDM_MINIMUM_CREDENTIAL_TYPE
        )
        return DEFAULT_KANIDM_MINIMUM_CREDENTIAL_TYPE


def set_kanidm_minimum_credential_type(minimum_credential_type: KanidmCredentialType):
    with WriteUserData() as data:
        if "kanidm" not in data:
            logger.warning("Missing 'kanidm' key in /etc/nixos/userdata.json.")

            data["kanidm"] = {"minimum_credential_type": minimum_credential_type.value}

        elif "minimum_credential_type" not in data["kanidm"]:
            logger.warning(
                "Missing 'minimum_credential_type' key in /etc/nixos/userdata.json."
            )

        data["kanidm"]["minimum_credential_type"] = minimum_credential_type.value
