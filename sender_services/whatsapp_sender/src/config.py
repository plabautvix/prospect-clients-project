import os

from dotenv import load_dotenv

load_dotenv()

CHANNEL = "whatsapp"

# ─── WAHA (WhatsApp HTTP API) ───────────────────────────────────────────────

WAHA_URL = os.getenv("WAHA_URL", "http://localhost:3000").rstrip("/")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
# WAHA Core serves a single session, and it must be called "default".
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30"))

# ─── Backend ────────────────────────────────────────────────────────────────

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000").rstrip("/")
# Service credential, separate from the user JWT. See ARCHITECTURE.md, S2.
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "dev-service-key-change-me")

# ─── Loop ───────────────────────────────────────────────────────────────────

# The backend may say "come back in six hours". Asking again sooner anyway is
# what notices a resumed campaign or a lifted pause, and keeps the worker
# showing as online.
MAX_WAIT_SECONDS = float(os.getenv("MAX_WAIT_SECONDS", "60"))
# While waiting for the QR scan, the code changes every few seconds.
DISCONNECTED_POLL_SECONDS = float(os.getenv("DISCONNECTED_POLL_SECONDS", "10"))
ERROR_DELAY_SECONDS = float(os.getenv("ERROR_DELAY_SECONDS", "15"))
