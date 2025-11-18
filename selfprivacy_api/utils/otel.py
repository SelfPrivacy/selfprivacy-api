import os

OTEL_ENABLED = os.environ.get("SP_API_OTEL_ENABLED") == "1"
