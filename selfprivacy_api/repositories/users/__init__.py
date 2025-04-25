# from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)

ACTIVE_USERS_PROVIDER = KanidmUserRepository  # JsonUserRepository
