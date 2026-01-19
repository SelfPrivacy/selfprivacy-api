from unittest.mock import AsyncMock

from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType
from tests.test_graphql.common import assert_empty, assert_ok, get_data

KANIDM_GET_MIN_QUERY = """
query MyQuery {
  kanidm {
    getMinimumKanidmCredentialType {
      minimumCredentialType
    }
  }
}
"""

KANIDM_SET_MIN_MUTATION = """
mutation MyMutation($minimumCredentialType: SetKanidmMinimumCredentialTypeInput!) {
  kanidmMutations {
    setKanidmMinimumCredentialType(minimumCredentialType: $minimumCredentialType) {
      code
      message
      minimumCredentialType
      success
    }
  }
}
"""


def test_graphql_get_minimum_kanidm_credential_type(authorized_client, mocker):
    mocker.patch(
        "selfprivacy_api.graphql.common_types.kanidm_credential_type.actions_get_kanidm_minimum_credential_type",
        new=AsyncMock(return_value=KanidmCredentialType.mfa),
    )

    response = authorized_client.post("/graphql", json={"query": KANIDM_GET_MIN_QUERY})
    data = get_data(response)

    assert (
        data["kanidm"]["getMinimumKanidmCredentialType"]["minimumCredentialType"]
        == "mfa"
    )


def test_graphql_set_minimum_kanidm_credential_type(authorized_client, mocker):
    mocker.patch(
        "selfprivacy_api.graphql.mutations.kanidm_mutations.set_kanidm_minimum_credential_type_action",
        new=AsyncMock(return_value=None),
    )

    response = authorized_client.post(
        "/graphql",
        json={
            "query": KANIDM_SET_MIN_MUTATION,
            "variables": {
                "minimumCredentialType": {"minimumCredentialType": "passkey"},
            },
        },
    )
    data = get_data(response)

    output = data["kanidmMutations"]["setKanidmMinimumCredentialType"]
    assert_ok(output, code=200)
    assert output["minimumCredentialType"] == "passkey"


def test_graphql_get_minimum_kanidm_credential_type_unauthorized(client):
    response = client.post("/graphql", json={"query": KANIDM_GET_MIN_QUERY})
    assert_empty(response)


def test_graphql_set_minimum_kanidm_credential_type_unauthorized(client):
    response = client.post(
        "/graphql",
        json={
            "query": KANIDM_SET_MIN_MUTATION,
            "variables": {
                "minimumCredentialType": {"minimumCredentialType": "passkey"},
            },
        },
    )
    assert_empty(response)
