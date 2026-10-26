import os
from pathlib import Path

from dotenv import load_dotenv

# Load back_end/.env (no-op if the file is absent). Variables already present in
# the environment (e.g. injected by docker-compose) take precedence over the file.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# JWT signing configuration, centralized so backend uses a single source of truth.
#
# JWT_SECRET MUST be provided via environment in any real deployment. The default
# below exists only so local development and the test suite work out of the box
# and is intentionally NOT secure.
JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-insecure-change-me")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

# Token lifetime. The user token is no longer propagated to internal services
# (they authenticate with SERVICE_API_KEY), so this can be tightened.
JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "720"))

# Shared secret for service-to-service authentication (maps-service -> backend),
# kept separate from user JWTs so services have their own identity and can be
# rotated/revoked independently. MUST be set via environment in real deployments.
SERVICE_API_KEY: str = os.getenv("SERVICE_API_KEY", "dev-service-key-change-me")

# How long a password reset link works. Short, since it grants the account to
# whoever holds the e-mail.
PASSWORD_RESET_EXPIRATION_MINUTES: int = int(
    os.getenv("PASSWORD_RESET_EXPIRATION_MINUTES", "30")
)

# Where the frontend lives, to build the links sent by e-mail.
APP_URL: str = os.getenv("APP_URL", "http://localhost").rstrip("/")
