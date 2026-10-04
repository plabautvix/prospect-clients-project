"""The login guard and the JS bridge of InstagramDM, without a browser."""

import asyncio
from types import SimpleNamespace

import pytest

import instagram
from instagram import InstagramDM, SessionState, TransientError


def run(coroutine):
    return asyncio.run(coroutine)


def _gateway(login, has_cookie=False):
    gateway = InstagramDM("conta", "senha")
    calls = {"login": 0}

    async def ensure_browser():
        return None

    async def cookie():
        return has_cookie

    async def fake_login():
        calls["login"] += 1
        return await login()

    async def close():
        return None

    gateway._ensure_browser = ensure_browser
    gateway._has_session_cookie = cookie
    gateway._login = fake_login
    gateway.close = close
    return gateway, calls


def test_an_unexpected_error_during_login_waits_for_the_user():
    # What happened in production: a JS bridge bug blew up mid-login, the
    # guard did not cover it, and the worker logged in again every cycle.
    async def broken_login():
        raise TypeError("'RemoteObject' object is not subscriptable")

    gateway, calls = _gateway(broken_login)

    first = run(gateway.session())
    second = run(gateway.session())
    third = run(gateway.session())

    assert calls["login"] == 1
    assert not first.ready
    assert "Entrar novamente" in first.detail
    assert second == third == first


def test_entrar_novamente_allows_one_more_attempt():
    async def broken_login():
        raise TypeError("boom")

    gateway, calls = _gateway(broken_login)
    run(gateway.session())

    gateway.reset()
    run(gateway.session())

    assert calls["login"] == 2


def test_automatic_logins_are_spaced_even_on_an_unforeseen_path():
    # A login that "works" but leaves no session cookie would otherwise
    # repeat on every cycle.
    async def login_without_cookie():
        return SessionState(True)

    gateway, calls = _gateway(login_without_cookie)

    run(gateway.session())
    later = run(gateway.session())

    assert calls["login"] == 1
    assert later.ready is False
    assert "min para tentar entrar de novo" in later.detail


def test_logged_in_means_no_login_at_all():
    async def login():
        raise AssertionError("must not log in")

    gateway, calls = _gateway(login, has_cookie=True)

    assert run(gateway.session()).ready is True
    assert calls["login"] == 0


class FakeTab:
    """Answers Runtime.evaluate like Chrome: (RemoteObject, ExceptionDetails)."""

    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error

    async def send(self, _command):
        return SimpleNamespace(value=self.value), self.error


def test_eval_returns_none_for_null_not_the_remote_object():
    # tab.evaluate returned the RemoteObject itself for null, and reading
    # ["x"] from it was the crash.
    gateway = InstagramDM("conta", "senha")
    gateway.tab = FakeTab(value=None)

    assert run(gateway._eval("null")) is None


def test_eval_returns_plain_values():
    gateway = InstagramDM("conta", "senha")
    gateway.tab = FakeTab(value={"x": 10, "y": 20})

    assert run(gateway._eval("({x: 10, y: 20})")) == {"x": 10, "y": 20}


def test_eval_raises_on_a_script_error():
    gateway = InstagramDM("conta", "senha")
    gateway.tab = FakeTab(error=SimpleNamespace(text="ReferenceError"))

    with pytest.raises(TransientError):
        run(gateway._eval("nope()"))


def test_click_text_does_nothing_when_the_button_is_not_there():
    gateway = InstagramDM("conta", "senha")
    gateway.tab = FakeTab(value=None)

    assert run(gateway._click_text(instagram.COOKIE_BANNER, timeout=0)) is False
