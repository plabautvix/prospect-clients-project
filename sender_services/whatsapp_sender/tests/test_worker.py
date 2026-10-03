import requests

import config
from backend import Claim, Message
from gateway import AccountError, PermanentError, SessionState, TransientError
from worker import Worker

MESSAGE = Message(id_message=7, recipient="5527998765432", body="Oi", attempts=1)


class FakeBackend:
    def __init__(self, claims=None, report_failures=0, reconnect=False):
        self.claims = list(claims or [])
        self.reports = []
        self.health_reports = []
        self.report_failures = report_failures
        self.reconnect = reconnect

    def claim(self):
        return self.claims.pop(0) if self.claims else Claim(None, 15)

    def report(self, message_id, outcome, error=None):
        if self.report_failures:
            self.report_failures -= 1
            raise requests.ConnectionError("backend down")
        self.reports.append((message_id, outcome, error))

    def health(self, state, detail=None, qr_code=None):
        self.health_reports.append((state, detail, qr_code))
        reconnect, self.reconnect = self.reconnect, False
        return reconnect


class FakeGateway:
    def __init__(self, state=SessionState(True), error=None):
        self.state = state
        self.error = error
        self.sent = []
        self.restarts = 0

    def restart(self):
        self.restarts += 1

    def session(self):
        if isinstance(self.state, Exception):
            raise self.state
        return self.state

    def send_text(self, phone, text):
        if self.error:
            raise self.error
        self.sent.append((phone, text))


def _worker(backend, gateway):
    return Worker(backend, gateway, sleep=lambda _: None)


def test_sends_and_reports():
    backend = FakeBackend([Claim(MESSAGE, None)])
    gateway = FakeGateway()

    delay = _worker(backend, gateway).run_once()

    assert gateway.sent == [("5527998765432", "Oi")]
    assert backend.reports == [(7, "sent", None)]
    assert delay == 0


def test_waits_as_long_as_the_backend_says_up_to_a_ceiling():
    worker = _worker(FakeBackend([Claim(None, 42)]), FakeGateway())
    assert worker.run_once() == 42

    worker = _worker(FakeBackend([Claim(None, 6 * 3600)]), FakeGateway())
    assert worker.run_once() == config.MAX_WAIT_SECONDS


def test_does_not_claim_while_disconnected():
    backend = FakeBackend([Claim(MESSAGE, None)])
    gateway = FakeGateway(SessionState(False, "Escaneie", "data:qr"))

    delay = _worker(backend, gateway).run_once()

    assert backend.claims  # untouched
    assert backend.health_reports == [("disconnected", "Escaneie", "data:qr")]
    assert delay == config.DISCONNECTED_POLL_SECONDS


def test_new_qr_code_asked_from_the_app_restarts_the_session():
    backend = FakeBackend(reconnect=True)
    gateway = FakeGateway(SessionState(False, "Escaneie", "data:old"))
    worker = _worker(backend, gateway)

    worker.run_once()
    worker.run_once()

    assert gateway.restarts == 1


def test_waha_down_is_reported():
    backend = FakeBackend()
    gateway = FakeGateway(TransientError("WAHA inacessivel"))

    _worker(backend, gateway).run_once()

    assert backend.health_reports[0][0] == "disconnected"


def test_outcomes_by_error_kind():
    cases = [
        (PermanentError("Numero sem WhatsApp."), "failed"),
        (TransientError("timeout"), "retry"),
        (AccountError("logged out"), "release"),
    ]
    for error, outcome in cases:
        backend = FakeBackend([Claim(MESSAGE, None)])
        _worker(backend, FakeGateway(error=error)).run_once()
        assert backend.reports == [(7, outcome, str(error))]


def test_account_error_also_shows_on_the_channel():
    backend = FakeBackend([Claim(MESSAGE, None)])
    _worker(backend, FakeGateway(error=AccountError("logged out"))).run_once()
    assert ("disconnected", "logged out", None) in backend.health_reports


def test_report_is_retried_until_it_lands():
    backend = FakeBackend([Claim(MESSAGE, None)], report_failures=3)

    _worker(backend, FakeGateway()).run_once()

    assert backend.reports == [(7, "sent", None)]


def test_ok_is_reported_once():
    backend = FakeBackend()
    worker = _worker(backend, FakeGateway())

    worker.run_once()
    worker.run_once()

    assert backend.health_reports == [("ok", None, None)]


def test_stop_ends_the_loop():
    backend = FakeBackend()
    worker = _worker(backend, FakeGateway())
    worker.stop()

    worker.run_forever()  # returns at once instead of looping

    assert backend.health_reports == []
