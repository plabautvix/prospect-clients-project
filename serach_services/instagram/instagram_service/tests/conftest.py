from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def results_html() -> str:
    return (FIXTURES / "serp.html").read_text(encoding="utf-8")
