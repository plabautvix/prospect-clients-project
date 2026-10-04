import os

from dotenv import load_dotenv

load_dotenv()

CHANNEL = "instagram"

# ─── Sender account ─────────────────────────────────────────────────────────

# A dedicated account, never the company's main one: automating Instagram goes
# against its terms and the account may be restricted.
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

# ─── Chrome ─────────────────────────────────────────────────────────────────

# Persisted, so the login survives restarts and is not repeated. Separate from
# the search service's profile: that one uses no account at all, and a
# restriction on this account must not touch it.
CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR", "")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

# ─── Backend ────────────────────────────────────────────────────────────────

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000").rstrip("/")
# Service credential, separate from the user JWT. See ARCHITECTURE.md, S2.
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "dev-service-key-change-me")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30"))

# ─── Loop ───────────────────────────────────────────────────────────────────

# The backend decides the pacing. Asking again at least this often notices a
# resumed campaign or a lifted pause, and keeps the worker showing as online.
MAX_WAIT_SECONDS = float(os.getenv("MAX_WAIT_SECONDS", "60"))
DISCONNECTED_POLL_SECONDS = float(os.getenv("DISCONNECTED_POLL_SECONDS", "10"))
ERROR_DELAY_SECONDS = float(os.getenv("ERROR_DELAY_SECONDS", "30"))
