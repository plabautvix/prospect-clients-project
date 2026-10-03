import re


def normalize_br_mobile(raw: str | None) -> str | None:
    """Turn a phone as Google Maps prints it into 55DDXXXXXXXXX.

    Returns None for anything that is not a Brazilian mobile: landlines rarely
    have WhatsApp, and sending to them only spends checks against the account.

    "(27) 99876-5432", "+55 27 99876-5432" and "027 99876-5432" all give
    "5527998765432".
    """
    if not raw:
        return None

    digits = re.sub(r"\D", "", raw)
    if len(digits) == 13 and digits.startswith("55"):
        digits = digits[2:]
    # Long distance prefix, as in 027 99876-5432.
    if len(digits) == 12 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) != 11:
        return None

    ddd, number = digits[:2], digits[2:]
    # No Brazilian area code contains a zero, and every mobile starts with 9.
    if "0" in ddd or not number.startswith("9"):
        return None

    return "55" + digits


_HANDLE = re.compile(r"^@?([A-Za-z0-9._]{1,30})$")


def instagram_handle(nome: str | None) -> str | None:
    """The handle of an Instagram lead, whose nome is stored as @handle."""
    if not nome:
        return None
    match = _HANDLE.match(nome.strip())
    return match.group(1).lower() if match else None
