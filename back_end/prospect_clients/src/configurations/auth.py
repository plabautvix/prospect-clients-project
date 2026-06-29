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

# Token lifetime. Kept generous for now because the user token is still propagated
# to and reused by the maps-service (see ARCHITECTURE.md, roadmap item 2). Once
# service identities replace that propagation, this should drop to ~15-60 minutes.
JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "720"))
