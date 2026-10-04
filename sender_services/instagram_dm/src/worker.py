"""The sending loop: session, claim, send, report, repeat.

Same contract as the WhatsApp sender. The pacing is decided by the backend,
which says how long to wait, so a restart changes nothing about the rhythm.

The gateway is async (nodriver), the loop is not: one event loop lives for the
whole process, so the browser it opened survives between messages.
"""

import asyncio
import logging
import threading
import time
from typing import Callable

import requests

import config
from backend import BackendClient, HealthAck, Message
from instagram import (
    AccountError,
    BlockedError,
    InstagramDM,
    PermanentError,
    TransientError,
)

logger = logging.getLogger(__name__)

REPORT_ATTEMPTS = 5


class Worker:
    def __init__(
        self,
        backend: BackendClient,
        gateway: InstagramDM,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._backend = backend
        self._gateway = gateway
        self._sleep = sleep
        self._stop = threading.Event()
        self._last_health: str | None = None
        self._loop = asyncio.new_event_loop()

    def _run(self, coroutine):
        return self._loop.run_until_complete(coroutine)

    def stop(self) -> None:
        self._stop.set()

    def run_forever(self) -> None:
        logger.info("Instagram sender started")
        try:
            while not self._stop.is_set():
                try:
                    delay = self.run_once()
                except requests.RequestException:
                    logger.exception("Backend unreachable")
                    delay = config.ERROR_DELAY_SECONDS
                self._stop.wait(delay)
        finally:
            self._run(self._gateway.close())
            self._loop.close()
        logger.info("Instagram sender stopped")

    def run_once(self) -> float:
        """One turn of the loop. Returns how long to wait before the next."""
        try:
            session = self._run(self._gateway.session())
        except (TransientError, AccountError) as error:
            self._report_health("disconnected", str(error))
            return config.ERROR_DELAY_SECONDS

        if not session.ready:
            ack = self._report_health("disconnected", session.detail, session.needs_code)
            self._handle_requests(ack)
            return config.DISCONNECTED_POLL_SECONDS

        self._report_health("ok")

        claim = self._backend.claim()
        if claim.message is None:
            wait = claim.retry_after_seconds or config.MAX_WAIT_SECONDS
            return min(max(wait, 1), config.MAX_WAIT_SECONDS)

        self._deliver(claim.message)
        # Straight back to the backend: it knows how long the gap must be.
        return 0

    def _handle_requests(self, ack: HealthAck) -> None:
        """Act on what the user asked for from the app."""
        if ack.reconnect:
            logger.info("Login requested from the app")
            self._gateway.reset()
        elif ack.verification_code:
            logger.info("Verification code received from the app")
            try:
                self._run(self._gateway.submit_code(ack.verification_code))
            except TransientError:
                logger.exception("Could not submit the verification code")

    def _deliver(self, message: Message) -> None:
        outcome, error = "sent", None
        try:
            self._run(self._gateway.send_text(message.recipient, message.body))
        except PermanentError as e:
            outcome, error = "failed", str(e)
        except TransientError as e:
            outcome, error = "retry", str(e)
        except BlockedError as e:
            # The backend pauses the channel; the message waits untouched.
            outcome, error = "release", str(e)
            self._report_health("blocked", str(e))
        except AccountError as e:
            outcome, error = "release", str(e)
            self._report_health("disconnected", str(e))

        logger.info(
            "Message %s to @%s: %s%s",
            message.id_message,
            message.recipient,
            outcome,
            f" ({error})" if error else "",
        )
        self._report(message.id_message, outcome, error)

    def _report(self, message_id: int, outcome: str, error: str | None) -> None:
        """Report, insisting: a lost "sent" report means the message goes out twice."""
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

    def _report_health(
        self, state: str, detail: str | None = None, needs_code: bool = False
    ) -> HealthAck:
        # "ok" only on change. Anything else every time, so the backend shows
        # the worker online and can hand over a code or a login request.
        if state == "ok" and self._last_health == "ok":
            return HealthAck()
        try:
            ack = self._backend.health(state, detail, needs_code)
            self._last_health = state
            return ack
        except requests.RequestException:
            logger.warning("Could not report health %s", state)
            return HealthAck()
