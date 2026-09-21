import os

from dotenv import load_dotenv

load_dotenv()

# ─── Chrome / search ────────────────────────────────────────────────────────

# Persisting the Chrome profile keeps cookies and the cookie-consent choice
# between runs, so the consent dialog only has to be accepted once, by hand.
CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR", "")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

# Seconds to wait between queries.
SEARCH_DELAY = float(os.getenv("SEARCH_DELAY", "6"))

# Safety ceiling, not the real stop. A run normally ends when Google stops
# offering a next page. Around 11s per page, so 20 pages is roughly 4 minutes.
MAX_PAGES = int(os.getenv("MAX_PAGES", "20"))

# ─── MQTT ───────────────────────────────────────────────────────────────────

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TLS = os.getenv("MQTT_TLS", "false").lower() == "true"
MQTT_CA_CERT = os.getenv("MQTT_CA_CERT", "")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "prospect/instagram")

# ─── Backend ────────────────────────────────────────────────────────────────

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
# Service credential, separate from the user JWT. See ARCHITECTURE.md, S2.
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "dev-service-key-change-me")
