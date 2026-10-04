import pytest

import pages

PROFILE = "https://www.instagram.com/padaria.sol/"


@pytest.mark.parametrize(
    "url, text, kind",
    [
        (PROFILE, "padaria.sol\nSeguir\nEnviar mensagem\n120 publicações", pages.OK),
        ("https://www.instagram.com/accounts/login/?next=/padaria.sol/", "Entrar", pages.LOGIN),
        ("https://www.instagram.com/challenge/action/", "Ajude-nos a confirmar", pages.CHALLENGE),
        ("https://www.instagram.com/accounts/suspended/", "", pages.SUSPENDED),
        (PROFILE, "Esta página não está disponível.\nO link pode estar quebrado.", pages.NOT_FOUND),
        (PROFILE, "Sorry, this page isn’t available.", pages.NOT_FOUND),
        (PROFILE, "Tente novamente mais tarde\nRestringimos determinadas atividades", pages.BLOCKED),
        (PROFILE, "Try Again Later", pages.BLOCKED),
    ],
)
def test_classify(url, text, kind):
    assert pages.classify(url, text) == kind


def test_the_url_wins_over_the_text():
    # A login page can mention anything; where we landed is what matters.
    assert pages.classify(
        "https://www.instagram.com/accounts/login/", "Esta página não está disponível"
    ) == pages.LOGIN


def test_code_screen():
    two_factor = "https://www.instagram.com/accounts/login/two_factor?next=%2F"
    assert pages.asks_for_code(two_factor, "Insira o código de segurança que enviamos")
    assert pages.asks_for_code(
        "https://www.instagram.com/challenge/", "Check your email. Enter the code we sent."
    )


def test_was_this_you_is_not_a_code_screen():
    assert not pages.asks_for_code(
        "https://www.instagram.com/challenge/", "Foi você? Confirme no app."
    )


def test_a_block_is_never_read_as_a_code_screen():
    assert not pages.asks_for_code(PROFILE, "Tente novamente mais tarde. Insira o código")


def test_wrong_password():
    assert pages.wrong_password("Sua senha está incorreta. Confira-a.")
    assert pages.wrong_password("Sorry, your password was incorrect.")
    assert not pages.wrong_password("Entrar com o Facebook")


def test_send_failed():
    assert pages.send_failed("Não foi possível enviar")
    assert pages.send_failed("Couldn’t send")
    assert not pages.send_failed("Oi, tudo bem?\nVisto")
