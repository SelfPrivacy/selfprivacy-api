import os

OAUTH_SECRET_PATH = "/run/keys/selfprivacy-api/kanidm-oauth-client-secret"
OAUTH_CLIENT_ID = "selfprivacy-api"


def load_oauth_client_secret():
    secret_path = OAUTH_SECRET_PATH
    if os.path.exists(secret_path):
        with open(secret_path, "r", encoding="utf-8") as secret_file:
            return secret_file.read().strip()
    else:
        raise FileNotFoundError(f"Secret file not found at {secret_path}")
