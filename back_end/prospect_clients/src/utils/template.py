import random
import re

# {Olá|Oi|E aí}: one option is picked per message. Identical text sent to many
# people is one of the clearest spam signals, and this is the cheapest way to
# avoid it. Only braces holding a | are variations, so {nome} is left alone.
_VARIATION = re.compile(r"\{([^{}]*\|[^{}]*)\}")
_PLACEHOLDER = re.compile(r"\{(nome|categoria)\}")

PLACEHOLDERS = ("nome", "categoria")


def render_message(
    template: str,
    nome: str | None,
    categoria: str | None,
    rng: random.Random | None = None,
) -> str:
    """Fill a message template for one lead.

    Variations are resolved first, so a lead's name is never read as one.
    Unknown placeholders are kept as typed, which makes a typo visible in the
    preview instead of silently disappearing.
    """
    rng = rng or random
    text = _VARIATION.sub(lambda m: rng.choice(m.group(1).split("|")), template)
    values = {"nome": nome or "", "categoria": categoria or ""}
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], text).strip()
