import pytest

from serp import instagram_handle, is_blocked, parse_results


def test_parses_every_organic_result(results_html):
    # Three profiles, one post, one external site. The pagination anchor has no
    # h3 and must not become a result.
    assert len(parse_results(results_html)) == 5


def test_first_result_has_title_url_and_snippet(results_html):
    first = parse_results(results_html)[0]

    assert first.url == "https://www.instagram.com/dra.anasilva.vet/"
    assert "@dra.anasilva.vet" in first.title
    assert "3.412 seguidores" in first.snippet


def test_snippet_excludes_the_title_and_the_neighbour(results_html):
    results = parse_results(results_html)

    assert "Dra. Ana Silva (@dra.anasilva.vet)" not in results[0].snippet
    assert "PetVida" not in results[0].snippet


def test_resolves_the_google_redirect(results_html):
    assert parse_results(results_html)[4].url == (
        "https://clinicaveterinariacampinas.com.br/equipe"
    )


def test_empty_html_gives_no_results():
    assert parse_results("") == []


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.instagram.com/dra.anasilva.vet/", "dra.anasilva.vet"),
        ("https://instagram.com/Vet_Paula", "vet_paula"),
        ("https://www.instagram.com/vet_paula_ramos?hl=pt-br", "vet_paula_ramos"),
        ("https://www.instagram.com/p/C9xYzAbCdEf/", None),
        ("https://www.instagram.com/explore/tags/vet/", None),
        ("https://clinicaveterinariacampinas.com.br/equipe", None),
    ],
)
def test_instagram_handle(url, expected):
    assert instagram_handle(url) == expected


def test_profiles_are_the_only_thing_kept(results_html):
    handles = [
        handle
        for result in parse_results(results_html)
        if (handle := instagram_handle(result.url))
    ]

    assert handles == ["dra.anasilva.vet", "clinica.petvida", "vet_paula_ramos"]


def test_block_page_is_not_confused_with_an_empty_page(results_html):
    assert is_blocked("https://www.google.com/sorry/index", "") is True
    assert is_blocked("https://www.google.com/search?q=x", "captcha-form") is True
    assert is_blocked("https://www.google.com/search?q=x", results_html) is False
