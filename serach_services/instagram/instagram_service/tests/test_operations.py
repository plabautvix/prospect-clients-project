import pytest

# operations imports search, which needs nodriver. Skip cleanly when it is not
# installed, so the serp tests still run on a bare checkout.
pytest.importorskip("nodriver")

from operations import build_query, to_leads  # noqa: E402
from serp import SearchResult  # noqa: E402


def test_build_query_scopes_the_search_to_instagram():
    assert build_query("medica veterinaria em Campinas") == (
        "site:instagram.com medica veterinaria em Campinas"
    )


def test_to_leads_uses_the_handle_as_the_upsert_key():
    profiles = {
        "dra.anasilva.vet": SearchResult(
            title="Dra. Ana Silva", url="https://www.instagram.com/dra.anasilva.vet/", snippet=""
        )
    }

    assert to_leads(profiles, "veterinaria Campinas") == [
        {
            "nome": "@dra.anasilva.vet",
            "site": "https://www.instagram.com/dra.anasilva.vet/",
            "categoria": "veterinaria Campinas",
        }
    ]


def test_to_leads_truncates_the_category_to_the_column_width():
    profiles = {"x": SearchResult(title="", url="https://instagram.com/x/", snippet="")}

    lead = to_leads(profiles, "a" * 200)[0]

    assert len(lead["categoria"]) == 100
