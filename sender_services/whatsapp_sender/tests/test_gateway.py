import pytest
import requests

from gateway import (
    AccountError,
    PermanentError,
    TransientError,
    WahaGateway,
    typing_seconds,
)


class FakeResponse:
    def __init__(self, status_code=200, json=None, text=""):
        self.status_code = status_code
        self._json = json or {}
        self.text = text
        self.ok = status_code < 400

    def json(self):
        return self._json


class FakeWaha:
    """Answers by (method, path); records every call."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []
        self.headers = {}

    def request(self, method, url, timeout=None, **kwargs):
        path = url.removeprefix("http://waha")
        self.calls.append((method, path, kwargs))
        answer = self.routes.get((method, path), FakeResponse())
        if isinstance(answer, Exception):
            raise answer
        return answer


def _gateway(routes):
    http = FakeWaha(routes)
    return WahaGateway("http://waha", "key", http=http, sleep=lambda _: None), http


class TestSession:
    def test_working(self):
        gateway, _ = _gateway(
            {("GET", "/api/sessions/default"): FakeResponse(json={"status": "WORKING"})}
        )
        assert gateway.session().ready is True

    def test_waiting_for_qr_returns_the_code(self):
        gateway, _ = _gateway(
            {
                ("GET", "/api/sessions/default"): FakeResponse(
                    json={"status": "SCAN_QR_CODE"}
                ),
                ("GET", "/api/default/auth/qr"): FakeResponse(
                    json={"mimetype": "image/png", "data": "AAA"}
                ),
            }
        )

        state = gateway.session()

        assert state.ready is False
        assert state.qr_code == "data:image/png;base64,AAA"

    def test_missing_session_is_created(self):
        gateway, http = _gateway({("GET", "/api/sessions/default"): FakeResponse(404)})

        assert gateway.session().ready is False
        assert ("POST", "/api/sessions") == http.calls[-1][:2]
        assert http.calls[-1][2]["json"] == {"name": "default", "start": True}

    def test_stopped_session_is_started(self):
        gateway, http = _gateway(
            {("GET", "/api/sessions/default"): FakeResponse(json={"status": "STOPPED"})}
        )

        gateway.session()

        assert ("POST", "/api/sessions/default/start") == http.calls[-1][:2]

    def test_failed_session_is_restarted_not_started(self):
        # WAHA ignores /start on a failed session ("already running"), which
        # left the screen with no QR code and no way out.
        gateway, http = _gateway(
            {("GET", "/api/sessions/default"): FakeResponse(json={"status": "FAILED"})}
        )

        state = gateway.session()

        assert state.ready is False
        assert ("POST", "/api/sessions/default/restart") == http.calls[-1][:2]

    def test_unreachable_is_transient(self):
        gateway, _ = _gateway(
            {("GET", "/api/sessions/default"): requests.ConnectionError("refused")}
        )
        with pytest.raises(TransientError):
            gateway.session()

    def test_bad_api_key_is_an_account_problem(self):
        gateway, _ = _gateway({("GET", "/api/sessions/default"): FakeResponse(401)})
        with pytest.raises(AccountError):
            gateway.session()


EXISTS = (
    ("GET", "/api/contacts/check-exists"),
    FakeResponse(json={"numberExists": True, "chatId": "552798765432@c.us"}),
)


class TestSendText:
    def test_sends_to_the_chat_id_whatsapp_knows(self):
        gateway, http = _gateway(dict([EXISTS]))

        gateway.send_text("5527998765432", "Oi")

        paths = [call[1] for call in http.calls]
        assert paths == [
            "/api/contacts/check-exists",
            "/api/startTyping",
            "/api/stopTyping",
            "/api/sendText",
        ]
        # The id WhatsApp returned, without the ninth digit, is the one used.
        assert http.calls[-1][2]["json"] == {
            "session": "default",
            "chatId": "552798765432@c.us",
            "text": "Oi",
        }

    def test_number_without_whatsapp_is_permanent(self):
        gateway, http = _gateway(
            {
                ("GET", "/api/contacts/check-exists"): FakeResponse(
                    json={"numberExists": False}
                )
            }
        )

        with pytest.raises(PermanentError):
            gateway.send_text("5527998765432", "Oi")
        assert len(http.calls) == 1

    def test_typing_failure_does_not_stop_the_message(self):
        gateway, http = _gateway(
            dict([EXISTS, (("POST", "/api/startTyping"), FakeResponse(500))])
        )

        gateway.send_text("5527998765432", "Oi")

        assert http.calls[-1][1] == "/api/sendText"

    def test_server_error_on_send_is_transient(self):
        gateway, _ = _gateway(dict([EXISTS, (("POST", "/api/sendText"), FakeResponse(503))]))
        with pytest.raises(TransientError):
            gateway.send_text("5527998765432", "Oi")

    def test_logged_out_session_is_an_account_problem(self):
        gateway, _ = _gateway(dict([EXISTS, (("POST", "/api/sendText"), FakeResponse(422))]))
        with pytest.raises(AccountError):
            gateway.send_text("5527998765432", "Oi")


def test_typing_time_is_bounded():
    assert typing_seconds("Oi") == 2.0
    assert typing_seconds("x" * 1000) == 8.0
