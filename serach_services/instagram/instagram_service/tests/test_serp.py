import pytest

from serp import (
    SearchResult,
    handle_from_cite,
    handle_from_title,
    handle_from_url,
    instagram_handle,
    is_blocked,
    parse_results,
)


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
def test_handle_from_url(url, expected):
    assert handle_from_url(url) == expected


@pytest.mark.parametrize(
    "title,expected",
    [
        # Titles captured from a live results page.
        ("Clinica Veterinaria 24h (@coracaoanimal.24h)", "coracaoanimal.24h"),
        ("Verum Diagnóstico Veterinário (@verumdiagnostico)", "verumdiagnostico"),
        (
            "Oncovida Veterinaria (@oncovidaveterinaria) · Campinas, SP",
            "oncovidaveterinaria",
        ),
        ("Late e Mia Campinas (@clinicalateemia)", "clinicalateemia"),
        ("Equipe - Clinica Veterinaria Campinas", None),
        ("", None),
    ],
)
def test_handle_from_title(title, expected):
    assert handle_from_title(title) == expected


def test_handle_falls_back_to_the_title_when_google_hides_the_url():
    # Google wraps result links in /goto?url=<blob>, so clean_url gives back an
    # empty string and the title is the only readable source.
    result = SearchResult(
        title="Clinica Veterinaria 24h (@coracaoanimal.24h)", url="", snippet=""
    )

    assert instagram_handle(result) == "coracaoanimal.24h"


def test_url_wins_over_the_title_when_both_are_present():
    result = SearchResult(
        title="Outro Nome (@do_titulo)",
        url="https://www.instagram.com/da_url/",
        snippet="",
    )

    assert instagram_handle(result) == "da_url"


def test_profiles_are_the_only_thing_kept(results_html):
    handles = [
        handle
        for result in parse_results(results_html)
        if (handle := instagram_handle(result))
    ]

    assert handles == ["dra.anasilva.vet", "clinica.petvida", "vet_paula_ramos"]


def test_block_page_is_detected_by_the_url():
    assert is_blocked("https://www.google.com/sorry/index", "<html></html>") is True


def test_block_page_is_detected_by_its_text_when_there_are_no_results():
    # Wording taken from the live block page.
    block = (
        "<html><body>Nossos sistemas detectaram tráfego incomum na sua rede"
        "</body></html>"
    )

    assert is_blocked("https://www.google.com/search?q=x", block) is True


def test_a_real_results_page_is_never_a_block(results_html):
    assert is_blocked("https://www.google.com/search?q=x", results_html) is False


def test_sorry_inside_the_body_is_not_a_block(results_html):
    # A live results page is hundreds of KB and mentions /sorry/ in its
    # scripts. Matching that in the body flagged every page as blocked.
    page = results_html + "<script>var u='/sorry/index';</script>"

    assert is_blocked("https://www.google.com/search?q=x", page) is False


def test_empty_response_is_a_block():
    assert is_blocked("https://www.google.com/search?q=x", "") is True


# Layout captured from a live results page in September 2026: the h3 sits
# inside an anchor whose href is an opaque /goto?url= redirect, and the real
# profile URL appears nowhere in the markup.
LIVE_LAYOUT = """
<div><div><div><div><div><div><div><div>
  <a href="/goto?url=CAESZAHrOzAVg2ss4N3eAWk4OcxkrVcY3D2V1FZ6vkchH"><span>
    <h3>Clinica Veterinaria 24h (@coracaoanimal.24h)</h3>
  </span></a>
  <div>Atendimento veterinario 24 horas em Campinas, urgencia e emergencia.</div>
</div></div></div></div></div></div></div></div>
<div><div><div><div><div><div><div><div>
  <a href="/goto?url=CAESYwHrOzAVK4aeN1BPPX0bK-aRXU2b9Bx3iCp0PoP9v"><span>
    <h3>Oncovida Veterinaria (@oncovidaveterinaria) &middot; Campinas, SP</h3>
  </span></a>
  <div>Oncologia veterinaria, quimioterapia e cuidados paliativos.</div>
</div></div></div></div></div></div></div></div>
"""


def test_live_layout_yields_handles_despite_the_goto_redirect():
    results = parse_results(LIVE_LAYOUT)

    assert len(results) == 2
    # clean_url cannot resolve /goto?url=, and that must not drop the result.
    assert all(r.url == "" for r in results)
    assert [instagram_handle(r) for r in results] == [
        "coracaoanimal.24h",
        "oncovidaveterinaria",
    ]


def test_live_layout_still_extracts_the_snippet():
    first = parse_results(LIVE_LAYOUT)[0]

    assert "Atendimento veterinario 24 horas" in first.snippet
    assert "Oncovida" not in first.snippet


# Real breadcrumbs, as Google renders them under the title.
@pytest.mark.parametrize(
    "cite,expected",
    [
        ("https://www.instagram.com › psicologapamelasoaltoe", "psicologapamelasoaltoe"),
        ("instagram.com › psi.danielalino", "psi.danielalino"),
        ("https://www.instagram.com/clinicacontinuar", "clinicacontinuar"),
        ("https://www.instagram.com › p › C9xYz", None),
        ("https://clinicaveterinaria.com.br › equipe", None),
        ("", None),
    ],
)
def test_handle_from_cite(cite, expected):
    assert handle_from_cite(cite) == expected


def test_truncated_title_falls_back_to_the_breadcrumb():
    # Google cuts long titles and takes the "(@handle)" with them. The
    # breadcrumb is rendered separately and survives.
    result = SearchResult(
        title="Inêz Torres I Psicanalista, Psicóloga CRP.16-ES 437, ...",
        url="",
        snippet="Atendimento em Vitória",
        cite="https://www.instagram.com › inez.torres.psi",
    )

    assert instagram_handle(result) == "inez.torres.psi"


def test_loose_handle_is_the_last_resort():
    result = SearchResult(
        title="Psicóloga em Vitória - atendimento online",
        url="",
        snippet="Agende pelo direct @psi.vitoria.es",
        cite="",
    )

    assert instagram_handle(result) == "psi.vitoria.es"


def test_a_result_with_no_handle_anywhere_is_dropped():
    result = SearchResult(
        title="Conselho Regional de Psicologia",
        url="",
        snippet="Registro profissional e orientações",
        cite="https://crp16.org.br › institucional",
    )

    assert instagram_handle(result) is None


def test_the_breadcrumb_is_extracted_from_the_live_layout():
    html = """
    <div><div><div>
      <a href="/goto?url=CAESZAHrOzAV"><span>
        <h3>Título muito longo que o Google cortou, ...</h3>
        <div><cite>https://www.instagram.com › psi.cortada</cite></div>
      </span></a>
      <div>Um snippet com tamanho suficiente para ser aceito aqui.</div>
    </div></div></div>
    """
    result = parse_results(html)[0]

    assert result.cite == "https://www.instagram.com › psi.cortada"
    assert instagram_handle(result) == "psi.cortada"
    # The breadcrumb lives inside the anchor and must not leak into the snippet.
    assert "instagram.com" not in result.snippet
