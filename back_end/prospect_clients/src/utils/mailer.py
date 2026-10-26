import logging
import smtplib
from email.message import EmailMessage

from prospect_clients.src.configurations.mail import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_STARTTLS,
    SMTP_TIMEOUT,
    SMTP_USERNAME,
)

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    """Send one e-mail. Failures are logged, never raised.

    It runs after the response has gone out, so there is nobody to raise to,
    and an error must not tell the caller whether the address has an account.
    """
    if not SMTP_HOST:
        logger.warning("SMTP_HOST is not set, e-mail %r was not sent", subject)
        return

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
            if SMTP_STARTTLS:
                smtp.starttls()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info("E-mail %r sent", subject)
    except (smtplib.SMTPException, OSError):
        logger.exception("Could not send e-mail %r", subject)
