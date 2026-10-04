"""Instagram direct messages through a real, logged in Chrome.

Instagram's official API only lets a business answer people who wrote first,
so reaching a lead means doing what a person does: open the profile, press
Message, type, press Enter. nodriver drives a headful Chrome under a virtual
display, as the search service does.

Errors are sorted by whose fault they are, because each one leads somewhere
different: a recipient that will never work, a hiccup worth retrying, an
account that cannot send right now, or an account Instagram is restricting.

Logging in is guarded on purpose. A refused password or a pending code makes
the gateway wait for the user instead of trying again: repeated logins are
what gets an account locked.
"""

import asyncio
import json
import logging
import math
import random
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import nodriver as uc
from nodriver import cdp

import pages

logger = logging.getLogger(__name__)

HOME_URL = "https://www.instagram.com/"
LOGIN_URL = "https://www.instagram.com/accounts/login/"
PROFILE_URL = "https://www.instagram.com/{}/"

MESSAGE_BUTTON = ("enviar mensagem", "message")
NOT_NOW = ("agora não", "not now")
COOKIE_BANNER = (
    "permitir todos os cookies",
    "allow all cookies",
    "recusar cookies opcionais",
    "decline optional cookies",
)

# The 2026 login form names them email and pass; the older one, username and
# password. Both are kept, newest first.
USERNAME_FIELD = ('input[name="email"]', 'input[name="username"]')
PASSWORD_FIELD = ('input[name="pass"]', 'input[name="password"]')
LOGIN_BUTTON = ("entrar", "log in")

TEXTBOX = (
    'div[role="textbox"][contenteditable="true"]',
    'div[contenteditable="true"][aria-label]',
    "textarea",
)
CODE_FIELD = (
    'input[name="code"]',
    'input[name="verificationCode"]',
    'input[name="security_code"]',
    'input[autocomplete="one-time-code"]',
    'input[inputmode="numeric"]',
)

CODE_DETAIL = (
    "O Instagram enviou um código de verificação por e-mail ou SMS para a conta "
    "remetente. Digite-o abaixo."
)

# Spacing between automatic login attempts. Repeated logins are what gets an
# account locked, so even a path nobody foresaw cannot log in more often.
MIN_LOGIN_INTERVAL_SECONDS = 10 * 60

# nodriver gives Chrome under three seconds to open its debugging port. A cold
# start on the persisted profile can take longer. Same as the search service.
LAUNCH_ATTEMPTS = 3


class PermanentError(Exception):
    """This recipient will never work: no such profile, no Message button."""


class TransientError(Exception):
    """Worth trying again later: a page that did not load, a browser hiccup."""


class AccountError(Exception):
    """The account cannot send right now: logged out, waiting for a code."""


class BlockedError(Exception):
    """Instagram is restricting the account ("Try again later")."""


@dataclass(frozen=True)
class SessionState:
    ready: bool
    detail: str | None = None
    needs_code: bool = False


def release_profile(profile_dir: str) -> None:
    """Make a persisted profile usable again after a run that ended badly.

    Kills a Chrome left holding this exact profile and removes the lock files
    Chrome never clears after an unclean exit. The `--` keeps pkill from
    reading the pattern, which starts with dashes, as its own option.
    """
    subprocess.run(
        ["pkill", "-f", "--", f"--user-data-dir={profile_dir}"],
        check=False,
        capture_output=True,
    )
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        Path(profile_dir, name).unlink(missing_ok=True)


def _center_of_text_js(texts: tuple[str, ...]) -> str:
    """JS that finds a visible button by its exact text and returns its center.

    Exact text, so "Message" never matches the "Messages" link of the sidebar.
    """
    return f"""(() => {{
  const wanted = {json.dumps(list(texts), ensure_ascii=False)};
  const els = [...document.querySelectorAll(
    'button, div[role="button"], a[role="button"], a[role="link"]'
  )];
  for (const want of wanted) {{
    const el = els.find(
      (e) => e.offsetParent !== null
        && (e.innerText || '').trim().toLowerCase() === want
    );
    if (el) {{
      el.scrollIntoView({{block: 'center'}});
      const r = el.getBoundingClientRect();
      return {{x: r.left + r.width / 2, y: r.top + r.height / 2}};
    }}
  }}
  return null;
}})()"""


def _textbox_count_js() -> str:
    return f"document.querySelectorAll('{TEXTBOX[0]}').length"


def _chat_is_with_js(handle: str) -> str:
    """JS: is the open conversation the one with this profile?

    Climbs from the message box to the nearest block holding links, which is
    the chat itself, and judges on that block alone. Climbing further would
    reach the profile page around it, which links to the profile whatever
    chat is open, and would approve the wrong conversation.
    """
    return f"""(() => {{
  const handle = {json.dumps(handle.lower())};
  let el = document.querySelector('{TEXTBOX[0]}');
  for (let i = 0; i < 20 && el; i++) {{
    el = el.parentElement;
    if (!el) return false;
    const links = [...el.querySelectorAll('a[href]')];
    if (!links.length) continue;
    return links
      .map((a) => a.getAttribute('href').toLowerCase().replace(/\\/+$/, ''))
      .some((href) => href === '/' + handle || href.endsWith('/' + handle));
  }}
  return false;
}})()"""


class InstagramDM:
    def __init__(
        self,
        username: str,
        password: str,
        profile_dir: str = "",
        headless: bool = False,
    ):
        self.username = username
        self.password = password
        self.profile_dir = profile_dir
        self.headless = headless
        self.browser = None
        self.tab = None
        # Waiting on the code screen: never log in again over it, that would
        # only send another code.
        self._awaiting_code = False
        # Why the last login did not work. Set means "wait for the user".
        self._login_failed: str | None = None
        self._last_login_at = float("-inf")

    # ─── Browser ─────────────────────────────────────────────────────────────

    async def _ensure_browser(self) -> None:
        if self.browser is not None:
            return

        options = {
            "headless": self.headless,
            "browser_args": [
                "--lang=pt-BR",
                "--disable-blink-features=AutomationControlled",
                # The container runs as root, and Chrome refuses to start as
                # root with its sandbox on.
                "--no-sandbox",
            ],
        }
        if self.profile_dir:
            options["user_data_dir"] = self.profile_dir

        for attempt in range(1, LAUNCH_ATTEMPTS + 1):
            if self.profile_dir:
                release_profile(self.profile_dir)
            try:
                self.browser = await uc.start(**options)
                break
            except Exception:
                if self.profile_dir:
                    release_profile(self.profile_dir)
                if attempt == LAUNCH_ATTEMPTS:
                    raise TransientError("O Chrome não abriu.")
                logger.warning("Chrome did not answer, attempt %d", attempt)
                await asyncio.sleep(2)

        self.tab = await self.browser.get(HOME_URL)
        await self._pause(3, 5)

    async def close(self) -> None:
        if self.browser is not None:
            try:
                self.browser.stop()
            except Exception:
                pass
        self.browser = None
        self.tab = None

    # ─── Page helpers ────────────────────────────────────────────────────────

    async def _pause(self, low: float, high: float) -> None:
        await asyncio.sleep(random.uniform(low, high))

    async def _eval(self, expression: str):
        """Run JS on the page and return its value, None for null.

        Not tab.evaluate: it hands back the raw RemoteObject whenever the
        value is falsy (null, "", 0), and the error details instead of raising.
        """
        remote, errors = await self.tab.send(
            cdp.runtime.evaluate(
                expression=expression,
                return_by_value=True,
                user_gesture=True,
                allow_unsafe_eval_blocked_by_csp=True,
            )
        )
        if errors:
            raise TransientError(f"Erro de script na página: {errors.text}")
        return remote.value if remote else None

    async def _visible(self) -> tuple[str, str]:
        """Current URL and visible text of the page."""
        # location.href and not tab.url: inside the app navigation is
        # client side, and the target's URL lags behind it.
        url = await self._eval("location.href")
        text = await self._eval("document.body ? document.body.innerText : ''")
        return url or "", text or ""

    async def _has_session_cookie(self) -> bool:
        cookies = await self.browser.cookies.get_all()
        return any(
            c.name == "sessionid" and c.value and "instagram" in (c.domain or "")
            for c in cookies
        )

    async def _drop_session_cookie(self) -> None:
        await self.tab.send(
            cdp.network.delete_cookies(name="sessionid", domain=".instagram.com")
        )

    async def _click_text(self, texts: tuple[str, ...], timeout: float = 0) -> bool:
        """Click a visible button by its text, with real mouse events."""
        deadline = time.monotonic() + timeout
        script = _center_of_text_js(texts)
        while True:
            position = await self._eval(script)
            if isinstance(position, dict):
                await self._pause(0.4, 1.0)
                await self.tab.mouse_click(position["x"], position["y"])
                return True
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(1)

    async def _first(self, selectors: tuple[str, ...], timeout: float = 10):
        deadline = time.monotonic() + timeout
        while True:
            for selector in selectors:
                element = await self.tab.query_selector(selector)
                if element is not None:
                    return element
            if time.monotonic() >= deadline:
                return None
            await asyncio.sleep(0.5)

    async def _key(self, key: str = "Enter", shift: bool = False) -> None:
        """A full keyDown/char/keyUp, which is what the page listens for.

        send_keys only dispatches `char` events: they insert text but never
        submit. Shift+Enter is a line break inside a message.
        """
        for event_type in ("keyDown", "char", "keyUp"):
            await self.tab.send(
                cdp.input_.dispatch_key_event(
                    type_=event_type,
                    modifiers=8 if shift else 0,
                    key=key,
                    code=key,
                    text="\r",
                    unmodified_text="\r",
                    windows_virtual_key_code=13,
                    native_virtual_key_code=13,
                )
            )

    async def _type(self, element, text: str) -> None:
        """Type in bursts, never paste: pasted text is a bot signal."""
        for char in text:
            if char == "\n":
                await self._key(shift=True)
            else:
                await element.send_keys(char)
            await asyncio.sleep(random.uniform(0.04, 0.18))
            if char == " " and random.random() < 0.25:
                await asyncio.sleep(random.uniform(0.2, 0.7))

    async def _dismiss_prompts(self) -> None:
        """Cookie banner, "Save your login info?", "Turn on notifications?"."""
        await self._click_text(COOKIE_BANNER, timeout=1)
        for _ in range(2):
            if await self._click_text(NOT_NOW, timeout=2):
                await self._pause(1, 2)

    # ─── Session ─────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """The user asked to log in again, after fixing whatever was wrong.

        A deliberate request, so it gets one attempt right away. Only
        automatic attempts are spaced.
        """
        self._awaiting_code = False
        self._login_failed = None
        self._last_login_at = float("-inf")

    async def session(self) -> SessionState:
        """Whether the account can send, logging in when it is not.

        Cheap when logged in: a cookie check, no navigation.

        A login attempt that fails in any way, foreseen or not, waits for the
        user. On top of that, automatic attempts are spaced by
        MIN_LOGIN_INTERVAL_SECONDS, so no path can turn into a login loop.
        """
        if self._awaiting_code:
            return SessionState(False, CODE_DETAIL, needs_code=True)
        if self._login_failed:
            return SessionState(False, self._login_failed)

        try:
            await self._ensure_browser()
            if await self._has_session_cookie():
                return SessionState(True)
        except (TransientError, AccountError):
            raise
        except Exception as error:
            await self.close()
            raise TransientError(f"Falha no navegador: {error}") from error

        wait = self._last_login_at + MIN_LOGIN_INTERVAL_SECONDS - time.monotonic()
        if wait > 0:
            return SessionState(
                False,
                f"Aguardando {math.ceil(wait / 60)} min para tentar entrar de novo.",
            )
        self._last_login_at = time.monotonic()

        try:
            return await self._login()
        except Exception as error:
            logger.exception("Login did not finish")
            await self.close()
            self._login_failed = (
                f"O login não terminou ({error}). Clique em Entrar novamente "
                "para tentar outra vez."
            )
            return SessionState(False, self._login_failed)

    async def _login(self) -> SessionState:
        if not self.username or not self.password:
            self._login_failed = (
                "Defina INSTAGRAM_USERNAME e INSTAGRAM_PASSWORD no .env do "
                "docker compose e reinicie o serviço."
            )
            return SessionState(False, self._login_failed)

        logger.info("Logging in as %s", self.username)
        self.tab = await self.browser.get(LOGIN_URL)
        await self._pause(3, 5)
        await self._click_text(COOKIE_BANNER, timeout=2)

        user_field = await self._first(USERNAME_FIELD, timeout=20)
        password_field = await self._first(PASSWORD_FIELD, timeout=5)
        if user_field is None or password_field is None:
            raise TransientError("A tela de login do Instagram não carregou.")

        await user_field.mouse_click()
        await self._type(user_field, self.username)
        await self._pause(0.5, 1.2)
        await password_field.mouse_click()
        await self._type(password_field, self.password)
        await self._pause(0.6, 1.5)
        # Clicking the button, as a person does. Enter only if it is not found.
        if not await self._click_text(LOGIN_BUTTON, timeout=3):
            await self._key()
        await self._pause(8, 11)

        return await self._after_login_step()

    async def _after_login_step(self) -> SessionState:
        """Read where a login or a code submission landed."""
        url, text = await self._visible()

        if pages.asks_for_code(url, text):
            self._awaiting_code = True
            return SessionState(False, CODE_DETAIL, needs_code=True)

        self._awaiting_code = False
        kind = pages.classify(url, text)
        if kind == pages.SUSPENDED:
            self._login_failed = "O Instagram suspendeu ou desativou a conta remetente."
        elif kind == pages.CHALLENGE:
            self._login_failed = (
                "O Instagram pediu uma confirmação. Abra o app do Instagram na "
                "conta remetente, confirme que foi você e clique em Entrar novamente."
            )
        elif await self._has_session_cookie():
            await self._dismiss_prompts()
            logger.info("Logged in")
            return SessionState(True)
        elif pages.wrong_password(text):
            self._login_failed = (
                "O Instagram recusou o usuário ou a senha. Corrija o .env, "
                "reinicie o serviço e clique em Entrar novamente."
            )
        else:
            self._login_failed = (
                "Não foi possível entrar no Instagram. Clique em Entrar novamente "
                "para tentar outra vez."
            )
        logger.warning("Login did not complete: %s", self._login_failed)
        return SessionState(False, self._login_failed)

    async def submit_code(self, code: str) -> SessionState:
        """Type the code the user received into the screen that asked for it."""
        if not self._awaiting_code or self.tab is None:
            return await self.session()
        try:
            field = await self._first(CODE_FIELD, timeout=5)
            if field is None:
                # The screen is gone (expired, or reloaded). Start over.
                self._awaiting_code = False
                return SessionState(False, "A tela do código expirou. Entrando de novo.")

            await field.mouse_click()
            await self._type(field, code)
            await self._pause(0.6, 1.4)
            await self._key()
            await self._pause(8, 11)

            state = await self._after_login_step()
            if state.needs_code:
                return SessionState(
                    False,
                    "O Instagram não aceitou o código. Confira e digite de novo.",
                    needs_code=True,
                )
            return state
        except Exception as error:
            # Same rule as a login: never start over on our own.
            logger.exception("Code submission did not finish")
            await self.close()
            self._awaiting_code = False
            self._login_failed = (
                f"O envio do código não terminou ({error}). Clique em Entrar "
                "novamente para tentar outra vez."
            )
            return SessionState(False, self._login_failed)

    # ─── Sending ─────────────────────────────────────────────────────────────

    async def send_text(self, handle: str, text: str) -> None:
        try:
            await self._send(handle, text)
        except (PermanentError, TransientError, AccountError, BlockedError):
            raise
        except Exception as error:
            await self.close()
            raise TransientError(f"Falha no navegador: {error}") from error

    async def _check_page(self) -> None:
        url, text = await self._visible()
        kind = pages.classify(url, text)

        if kind == pages.LOGIN:
            # Instagram ended the session. Forget it, so the next session
            # check logs in again instead of trusting a dead cookie.
            await self._drop_session_cookie()
            raise AccountError("O Instagram encerrou a sessão da conta remetente.")
        if kind in (pages.CHALLENGE, pages.SUSPENDED):
            state = await self._after_login_step()
            raise AccountError(state.detail or "A conta remetente precisa de atenção.")
        if kind == pages.BLOCKED:
            raise BlockedError("O Instagram está limitando a conta: 'Tente novamente mais tarde'.")
        if kind == pages.NOT_FOUND:
            raise PermanentError("Perfil não encontrado.")

    async def _send(self, handle: str, text: str) -> None:
        await self._ensure_browser()

        self.tab = await self.browser.get(PROFILE_URL.format(handle))
        # Looking at the profile for a moment, as anyone would.
        await self._pause(3, 6)
        await self._check_page()

        # A conversa já aberta antes do clique seria de outra pessoa.
        if await self._eval(_textbox_count_js()):
            raise TransientError("Havia outra conversa aberta; nada foi digitado.")

        if not await self._click_text(MESSAGE_BUTTON, timeout=8):
            raise PermanentError("O perfil não mostra o botão de mensagem.")

        # Since 2026 the button opens a floating chat over the profile instead
        # of navigating to /direct/. Either way, the conversation is ready
        # when its text box shows up.
        deadline = time.monotonic() + 20
        while not await self._eval(_textbox_count_js()):
            if time.monotonic() >= deadline:
                await self._check_page()
                raise TransientError("A conversa não abriu.")
            await asyncio.sleep(1)

        await self._pause(2, 4)
        await self._dismiss_prompts()

        # Never type without knowing whose conversation this is: one box, and
        # it belongs to a chat that links to this profile.
        if await self._eval(_textbox_count_js()) != 1:
            raise TransientError("Mais de uma conversa aberta; nada foi digitado.")
        if not await self._eval(_chat_is_with_js(handle)):
            raise TransientError(
                f"Não deu para confirmar que a conversa aberta é com @{handle}; "
                "nada foi digitado."
            )

        box = await self._first(TEXTBOX, timeout=5)
        if box is None:
            await self._check_page()
            raise TransientError("A caixa de mensagem não apareceu.")

        await box.mouse_click()
        await self._pause(0.5, 1.5)
        await self._type(box, text)
        # Reading it over before sending.
        await self._pause(1, 2.5)
        await self._key()
        await self._pause(2.5, 4)

        await self._check_page()
        _, visible = await self._visible()
        if pages.send_failed(visible):
            raise TransientError("O Instagram não conseguiu enviar a mensagem.")

        box = await self._first(TEXTBOX, timeout=3)
        if box is not None:
            left = await box.apply("(e) => e.innerText")
            # apply returns the error details, not a string, if the box went
            # stale; only real leftover text means the message did not go.
            if isinstance(left, str) and left.strip():
                raise TransientError("A mensagem ficou na caixa de texto, não saiu.")
