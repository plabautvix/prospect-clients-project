"""What an Instagram page is, from its URL and its visible text.

Only visible text (document.body.innerText) is read, never the HTML. The page
source carries every translated string of the app inside its scripts, so
"Try again later" is in the HTML of a perfectly normal page.

Markers come in Portuguese and English: the browser runs in pt-BR, but
Instagram does not always honour it.
"""

OK = "ok"
LOGIN = "login"
CHALLENGE = "challenge"
SUSPENDED = "suspended"
BLOCKED = "blocked"
NOT_FOUND = "not_found"

_LOGIN_URL = ("/accounts/login",)
_CHALLENGE_URL = ("/challenge", "/two_factor", "/auth_platform/codeentry")
_SUSPENDED_URL = ("/accounts/suspended", "/accounts/disabled")

# Instagram's soft block on an account that is acting too fast.
_BLOCKED_TEXT = (
    "try again later",
    "tente novamente mais tarde",
    "we restrict certain activity",
    "restringimos determinadas atividades",
    "action blocked",
    "ação bloqueada",
)

_NOT_FOUND_TEXT = (
    "this page isn't available",
    "esta página não está disponível",
    "page not found",
    "página não encontrada",
)

_WRONG_PASSWORD_TEXT = (
    "password was incorrect",
    "password you entered is incorrect",
    "senha incorreta",
    "senha está incorreta",
    "senha inserida está incorreta",
)

_CODE_TEXT = (
    "security code",
    "código de segurança",
    "confirmation code",
    "código de confirmação",
    "enter the code",
    "insira o código",
    "digite o código",
    "check your email",
    "verifique seu email",
    "verifique seu e-mail",
)

_SEND_FAILED_TEXT = (
    "couldn't send",
    "failed to send",
    "não foi possível enviar",
    "falha ao enviar",
)


def _norm(text: str | None) -> str:
    # Instagram mixes typographic and plain apostrophes.
    return (text or "").replace("’", "'").lower()


def classify(url: str, text: str) -> str:
    u, t = _norm(url), _norm(text)
    if any(m in u for m in _SUSPENDED_URL):
        return SUSPENDED
    if any(m in u for m in _CHALLENGE_URL):
        return CHALLENGE
    if any(m in u for m in _LOGIN_URL):
        return LOGIN
    if any(m in t for m in _BLOCKED_TEXT):
        return BLOCKED
    if any(m in t for m in _NOT_FOUND_TEXT):
        return NOT_FOUND
    return OK


def asks_for_code(url: str, text: str) -> bool:
    """A screen waiting for a code sent by e-mail or SMS.

    A challenge without a code field ("Was this you?") is not one: that is
    answered in the Instagram app, not here.
    """
    if classify(url, text) in (BLOCKED, SUSPENDED):
        return False
    return any(m in _norm(text) for m in _CODE_TEXT)


def wrong_password(text: str) -> bool:
    return any(m in _norm(text) for m in _WRONG_PASSWORD_TEXT)


def send_failed(text: str) -> bool:
    return any(m in _norm(text) for m in _SEND_FAILED_TEXT)
