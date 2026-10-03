"""WhatsApp through WAHA, a self-hosted WhatsApp Web gateway.

The worker only knows WhatsAppGateway. Moving to the official Cloud API later
means writing another class with the same two methods.

Errors are sorted by whose fault they are, because each one leads somewhere
different: a recipient that will never work, a hiccup worth retrying, or an
account that cannot send anything right now.
"""

import logging
import time
from dataclasses import dataclass
from typing import Callable, Protocol

import requests

logger = logging.getLogger(__name__)


class PermanentError(Exception):
    """This recipient will never work: no WhatsApp on the number, bad id."""


class TransientError(Exception):
    """Worth trying again later: timeout, gateway error."""


class AccountError(Exception):
    """The account cannot send at all right now: logged out, bad API key."""


@dataclass(frozen=True)
class SessionState:
    ready: bool
    detail: str | None = None
    qr_code: str | None = None


class WhatsAppGateway(Protocol):
    def session(self) -> SessionState: ...

    def restart(self) -> None: ...

    def send_text(self, phone: str, text: str) -> None: ...


def typing_seconds(text: str) -> float:
    """How long to show "typing..." before a message goes out.

    A message that appears with no typing at all is a bot signal. This is not
    meant to match a real typist, only to look like someone wrote it.
    """
    return min(8.0, max(2.0, len(text) / 15))


class WahaGateway:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        session: str = "default",
        timeout: float = 30,
        http: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._base = base_url
        self._session = session
        self._timeout = timeout
        self._sleep = sleep
        self._http = http or requests.Session()
        if api_key:
            self._http.headers.update({"X-Api-Key": api_key})

    # ─── HTTP ────────────────────────────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            response = self._http.request(
                method, f"{self._base}{path}", timeout=self._timeout, **kwargs
            )
        except requests.RequestException as error:
            raise TransientError(f"WAHA inacessivel: {error}") from error

        if response.status_code == 401:
            raise AccountError("WAHA recusou a chave de API (WAHA_API_KEY).")
        if response.status_code >= 500:
            raise TransientError(f"WAHA respondeu {response.status_code}: {response.text[:200]}")
        return response

    # ─── Session ─────────────────────────────────────────────────────────────

    def session(self) -> SessionState:
        """Where the WhatsApp login stands, starting it when it is not running.

        Raises TransientError when WAHA itself cannot be reached.
        """
        response = self._request("GET", f"/api/sessions/{self._session}")
        if response.status_code == 404:
            self._request("POST", "/api/sessions", json={"name": self._session, "start": True})
            return SessionState(False, "Iniciando a sessao do WhatsApp.")

        status = response.json().get("status")
        if status == "WORKING":
            return SessionState(True)
        if status == "SCAN_QR_CODE":
            return SessionState(
                False,
                "Escaneie o QR code com o WhatsApp do numero que vai enviar.",
                self._qr_code(),
            )
        if status == "STOPPED":
            logger.warning("WAHA session is stopped, starting it")
            self._request("POST", f"/api/sessions/{self._session}/start")
            return SessionState(False, "Sessao parada, iniciando.")
        if status == "FAILED":
            # /start is a no-op here: WAHA counts a failed session as running.
            # It fails when a QR code expires unscanned or a link attempt is
            # refused, and only a restart brings a fresh code.
            logger.warning("WAHA session failed, restarting it")
            self.restart()
            return SessionState(False, "A sessao caiu. Gerando um novo QR code.")
        return SessionState(False, "Iniciando a sessao do WhatsApp.")

    def restart(self) -> None:
        """Restart the session from scratch, which yields a new QR code."""
        self._request("POST", f"/api/sessions/{self._session}/restart")

    def _qr_code(self) -> str | None:
        response = self._request(
            "GET",
            f"/api/{self._session}/auth/qr",
            params={"format": "image"},
            headers={"Accept": "application/json"},
        )
        if not response.ok:
            return None
        data = response.json()
        return f"data:{data.get('mimetype', 'image/png')};base64,{data['data']}"

    # ─── Sending ─────────────────────────────────────────────────────────────

    def _chat_id(self, phone: str) -> str:
        """The chat id WhatsApp uses for a number, or PermanentError.

        Asking first matters in Brazil: some older numbers are registered
        without the ninth digit, and only WhatsApp knows which form is real.
        """
        response = self._request(
            "GET",
            "/api/contacts/check-exists",
            params={"phone": phone, "session": self._session},
        )
        self._raise_for_client_error(response)
        data = response.json()
        if not data.get("numberExists"):
            raise PermanentError("Numero sem WhatsApp.")
        return data.get("chatId") or f"{phone}@c.us"

    def _raise_for_client_error(self, response: requests.Response) -> None:
        if response.status_code == 404:
            raise AccountError("Sessao do WhatsApp nao encontrada no WAHA.")
        if response.status_code == 422:
            # WAHA answers 422 when the session exists but is not logged in.
            raise AccountError(f"Sessao do WhatsApp indisponivel: {response.text[:200]}")
        if 400 <= response.status_code < 500:
            raise PermanentError(f"WAHA recusou: {response.status_code} {response.text[:200]}")

    def _typing(self, action: str, chat_id: str) -> None:
        # Cosmetic: a failure here must never stop the message.
        try:
            self._request(
                "POST", f"/api/{action}", json={"session": self._session, "chatId": chat_id}
            )
        except (TransientError, AccountError):
            logger.debug("Could not %s for %s", action, chat_id)

    def send_text(self, phone: str, text: str) -> None:
        chat_id = self._chat_id(phone)

        self._typing("startTyping", chat_id)
        self._sleep(typing_seconds(text))
        self._typing("stopTyping", chat_id)

        response = self._request(
            "POST",
            "/api/sendText",
            json={"session": self._session, "chatId": chat_id, "text": text},
        )
        self._raise_for_client_error(response)
