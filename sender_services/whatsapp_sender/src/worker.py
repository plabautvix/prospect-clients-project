"""The sending loop: claim, send, report, repeat.

The pacing is not here. The backend decides when the next message may go out
and says how long to wait, so a restart of this worker changes nothing about
the rhythm: it asks again and is told the same thing.
"""

import logging
import threading
import time
from typing import Callable

import requests

import config
from backend import BackendClient, Message
from gateway import AccountError, PermanentError, TransientError, WhatsAppGateway

logger = logging.getLogger(__name__)

REPORT_ATTEMPTS = 5


class Worker:
    def __init__(
        self,
        backend: BackendClient,
        gateway: WhatsAppGateway,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._backend = backend
        self._gateway = gateway
        self._sleep = sleep
        self._stop = threading.Event()
        self._last_health: str | None = None

    def stop(self) -> None:
        self._stop.set()

    def run_forever(self) -> None:
        logger.info("WhatsApp sender started")
        while not self._stop.is_set():
            try:
                delay = self.run_once()
            except requests.RequestException:
                logger.exception("Backend unreachable")
                delay = config.ERROR_DELAY_SECONDS
            # Event.wait instead of sleep, so a stop request ends the wait.
            self._stop.wait(delay)
        logger.info("WhatsApp sender stopped")

    def run_once(self) -> float:
        """One turn of the loop. Returns how long to wait before the next."""
        try:
            session = self._gateway.session()
        except (TransientError, AccountError) as error:
            self._report_health("disconnected", str(error))
            return config.ERROR_DELAY_SECONDS

        if not session.ready:
            if self._report_health("disconnected", session.detail, session.qr_code):
                self._restart_session()
            return config.DISCONNECTED_POLL_SECONDS

        self._report_health("ok")

        claim = self._backend.claim()
        if claim.message is None:
            wait = claim.retry_after_seconds or config.MAX_WAIT_SECONDS
            return min(max(wait, 1), config.MAX_WAIT_SECONDS)

        self._deliver(claim.message)
        # Straight back to the backend: it knows how long the gap must be.
        return 0

    def _deliver(self, message: Message) -> None:
        outcome, error = "sent", None
        try:
            self._gateway.send_text(message.recipient, message.body)
        except PermanentError as e:
            outcome, error = "failed", str(e)
        except TransientError as e:
            outcome, error = "retry", str(e)
        except AccountError as e:
            # Not the message's fault: hand it back and show the account state.
            outcome, error = "release", str(e)
            self._report_health("disconnected", str(e))

        logger.info(
            "Message %s to %s: %s%s",
            message.id_message,
            message.recipient,
            outcome,
            f" ({error})" if error else "",
        )
        self._report(message.id_message, outcome, error)

    def _report(self, message_id: int, outcome: str, error: str | None) -> None:
        """Report, insisting: a lost "sent" report means the message goes out twice.

        If every attempt fails, the lease ends and the message is sent again.
        That is the price of never losing one.
        """
        for attempt in range(1, REPORT_ATTEMPTS + 1):
            try:
                self._backend.report(message_id, outcome, error)
                return
            except requests.RequestException:
                logger.warning(
                    "Report of message %s failed (%d/%d)",
                    message_id,
                    attempt,
                    REPORT_ATTEMPTS,
                )
                if attempt < REPORT_ATTEMPTS:
                    self._sleep(2**attempt)
        logger.error("Could not report message %s as %s", message_id, outcome)

    def _restart_session(self) -> None:
        """The user asked for a new QR code from the app."""
        logger.info("New session requested from the app, restarting it")
        try:
            self._gateway.restart()
        except (TransientError, AccountError):
            logger.exception("Could not restart the WhatsApp session")

    def _report_health(
        self, state: str, detail: str | None = None, qr_code: str | None = None
    ) -> bool:
        """Report the account state. True when the user asked for a new session."""
        # "ok" only on change. Anything else every time: the QR code rotates,
        # and the backend shows the worker as online while it hears from it.
        if state == "ok" and self._last_health == "ok":
            return False
        try:
            reconnect = self._backend.health(state, detail, qr_code)
            self._last_health = state
            return reconnect
        except requests.RequestException:
            logger.warning("Could not report health %s", state)
            return False
