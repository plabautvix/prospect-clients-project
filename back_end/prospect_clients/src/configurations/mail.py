import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# Outgoing e-mail. Without SMTP_HOST nothing is sent and a warning is logged,
# so the app still runs where no mail server is configured. In docker-compose
# the default is Mailpit, which keeps every message for viewing in a browser.
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_STARTTLS: bool = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
SMTP_FROM: str = os.getenv("SMTP_FROM", "Prospect <nao-responda@prospect.app>")
SMTP_TIMEOUT: float = float(os.getenv("SMTP_TIMEOUT", "15"))
