import requests

import config
from backend import Claim, HealthAck, Message
from instagram import (
    AccountError,
    BlockedError,
    PermanentError,
    SessionState,
    TransientError,
)
from worker import Worker

MESSAGE = Message(id_message=7, recipient="padaria.sol", body="Oi", attempts=1)


class FakeBackend:
    def __init__(self, claims=None, acks=None, report_failures=0):
        self.claims = list(claims or [])
        self.acks = list(acks or [])
        self.reports = []
        self.health_reports = []
        self.report_failures = report_failures

    def claim(self):
        return self.claims.pop(0) if self.claims else Claim(None, 15)

    def report(self, message_id, outcome, error=None):
        if self.report_failures:
            self.report_failures -= 1
            raise requests.ConnectionError("backend down")
        self.reports.append((message_id, outcome, error))

    def health(self, state, detail=None, needs_code=False):
        self.health_reports.append((state, detail, needs_code))
        return self.acks.pop(0) if self.acks else HealthAck()


class FakeGateway:
    def __init__(self, state=SessionState(True), error=None):
        self.state = state
        self.error = error
        self.sent = []
        self.codes = []
        self.resets = 0
        self.closed = False

    async def session(self):
        if isinstance(self.state, Exception):
            raise self.state
        return self.state

    async def send_text(self, handle, text):
        if self.error:
            raise self.error
        self.sent.append((handle, text))

    async def submit_code(self, code):
        self.codes.append(code)
        return SessionState(True)

    def reset(self):
        self.resets += 1

    async def close(self):
        self.closed = True


def _worker(backend, gateway):
    return Worker(backend, gateway, sleep=lambda _: None)


def test_sends_and_reports():
    backend = FakeBackend([Claim(MESSAGE, None)])
    gateway = FakeGateway()

    delay = _worker(backend, gateway).run_once()

    assert gateway.sent == [("padaria.sol", "Oi")]
    assert backend.reports == [(7, "sent", None)]
    assert delay == 0


def test_waits_as_long_as_the_backend_says_up_to_a_ceiling():
    assert _worker(FakeBackend([Claim(None, 42)]), FakeGateway()).run_once() == 42
    assert (
        _worker(FakeBackend([Claim(None, 9 * 3600)]), FakeGateway()).run_once()
        == config.MAX_WAIT_SECONDS
    )


def test_does_not_claim_while_logged_out():
    backend = FakeBackend([Claim(MESSAGE, None)])
    gateway = FakeGateway(SessionState(False, "Senha recusada"))

    delay = _worker(backend, gateway).run_once()

    assert backend.claims  # untouched
    assert backend.health_reports == [("disconnected", "Senha recusada", False)]
    assert delay == config.DISCONNECTED_POLL_SECONDS


def test_code_screen_is_reported_and_the_typed_code_reaches_instagram():
    backend = FakeBackend(acks=[HealthAck(verification_code="123456")])
    gateway = FakeGateway(SessionState(False, "Digite o código", needs_code=True))

    _worker(backend, gateway).run_once()

    assert backend.health_reports == [("disconnected", "Digite o código", True)]
    assert gateway.codes == ["123456"]


def test_login_again_asked_from_the_app():
    backend = FakeBackend(acks=[HealthAck(reconnect=True)])
    gateway = FakeGateway(SessionState(False, "Senha recusada"))

    _worker(backend, gateway).run_once()

    assert gateway.resets == 1


def test_browser_failure_is_reported():
    backend = FakeBackend()
    gateway = FakeGateway(TransientError("O Chrome não abriu."))

    delay = _worker(backend, gateway).run_once()

    assert backend.health_reports == [("disconnected", "O Chrome não abriu.", False)]
    assert delay == config.ERROR_DELAY_SECONDS


def test_outcomes_by_error_kind():
    cases = [
        (PermanentError("Perfil não encontrado."), "failed"),
        (TransientError("A conversa não abriu."), "retry"),
        (AccountError("Sessão encerrada"), "release"),
        (BlockedError("Tente novamente mais tarde"), "release"),
    ]
    for error, outcome in cases:
        backend = FakeBackend([Claim(MESSAGE, None)])
        _worker(backend, FakeGateway(error=error)).run_once()
        assert backend.reports == [(7, outcome, str(error))]


def test_restriction_pauses_the_channel():
    backend = FakeBackend([Claim(MESSAGE, None)])

    _worker(backend, FakeGateway(error=BlockedError("Tente novamente mais tarde"))).run_once()

    assert ("blocked", "Tente novamente mais tarde", False) in backend.health_reports


def test_report_is_retried_until_it_lands():
    backend = FakeBackend([Claim(MESSAGE, None)], report_failures=3)

    _worker(backend, FakeGateway()).run_once()

    assert backend.reports == [(7, "sent", None)]


def test_ok_is_reported_once():
    backend = FakeBackend()
    worker = _worker(backend, FakeGateway())

    worker.run_once()
    worker.run_once()

    assert backend.health_reports == [("ok", None, False)]


def test_stop_closes_the_browser():
    gateway = FakeGateway()
    worker = _worker(FakeBackend(), gateway)
    worker.stop()

    worker.run_forever()

    assert gateway.closed is True
