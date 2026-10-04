"""The backend's outbox, as seen from a sender worker.

Same contract as the WhatsApp sender: the worker never touches the database,
it asks for the next message and reports back.
"""

from dataclasses import dataclass

import requests

import config


@dataclass(frozen=True)
class Message:
    id_message: int
    recipient: str
    body: str
    attempts: int


@dataclass(frozen=True)
class Claim:
    message: Message | None
    retry_after_seconds: float | None


@dataclass(frozen=True)
class HealthAck:
    """What the user asked for from the app since the last report."""

    reconnect: bool = False
    verification_code: str | None = None


class BackendClient:
    def __init__(self, http: requests.Session | None = None):
        self._http = http or requests.Session()
        self._http.headers.update({"X-Service-Key": config.SERVICE_API_KEY})
        self._base = f"{config.BACKEND_API_URL}/outbox"

    def _post(self, path: str, json: dict | None = None) -> dict:
        response = self._http.post(
            f"{self._base}{path}", json=json, timeout=config.HTTP_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def claim(self) -> Claim:
        data = self._post(f"/{config.CHANNEL}/claim")
        message = data.get("message")
        return Claim(
            message=Message(**message) if message else None,
            retry_after_seconds=data.get("retry_after_seconds"),
        )

    def report(self, message_id: int, outcome: str, error: str | None = None) -> None:
        self._post(
            f"/messages/{message_id}/result",
            {"outcome": outcome, "error": error[:500] if error else None},
        )

    def health(
        self, state: str, detail: str | None = None, needs_code: bool = False
    ) -> HealthAck:
        data = self._post(
            f"/{config.CHANNEL}/health",
            {"state": state, "detail": detail, "needs_code": needs_code},
        )
        return HealthAck(
            reconnect=bool(data.get("reconnect")),
            verification_code=data.get("verification_code"),
        )
