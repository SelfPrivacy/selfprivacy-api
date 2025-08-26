from selfprivacy_api.utils import ReadUserData

from selfprivacy_api.models.kanidm_credential_lvl import KanidmCredentialLvl


# TODO: errors


class KanidmCredentialLvlNotFound(Exception):
    """Key not found"""

    @staticmethod
    def get_error_message() -> str:
        return "Missing 'kanidm_credential_lvl' key in /etc/nixos/userdata.json"


class InvalidKanidmCredentialLvl(Exception):
    """Invalid Kanidm Credential Lvl"""

    @staticmethod
    def get_error_message() -> str:
        return """
        Invalid value 'kanidm_credential_lvl'
        for enum 'KanidmCredentialLvl' in /etc/nixos/userdata.json.
        Support only ANY, MFA, PASSKEY.
        See https://kanidm.github.io/kanidm/stable/accounts/account_policy.html
        """


def get_kanidm_credential_lvl() -> KanidmCredentialLvl:
    with ReadUserData() as data:
        if "kanidm_credential_lvl" not in data:
            raise KanidmCredentialLvlNotFound()

        raw = data["kanidm_credential_lvl"]
        try:
            return KanidmCredentialLvl(str(raw).upper())
        except ValueError:
            raise InvalidKanidmCredentialLvl(f"Unsupported level: {raw}")
