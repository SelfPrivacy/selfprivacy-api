from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.actions.users import delete_user

"""
    A place for user storage tests and other user tests that are not Graphql-specific.
"""

# yes it is an incomplete suite.
# It was born in order to not lose things that REST API tests checked for
# In the future, user storage tests that are not dependent on actual API (graphql or otherwise) go here.


def test_delete_user_writes_json(generic_userdata):
    delete_user("user2")
    with ReadUserData() as data:
        assert data["users"] == [
            {
                "username": "user1",
                "hashedPassword": "HASHED_PASSWORD_1",
                "sshKeys": ["ssh-rsa KEY user1@pc"],
            },
            {
                "username": "user3",
                "hashedPassword": "HASHED_PASSWORD_3",
                "sshKeys": ["ssh-rsa KEY user3@pc"],
            },
        ]
