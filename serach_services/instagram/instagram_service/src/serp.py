"""Turn a Google results page into structured results."""

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from lxml import html as lxml_html

# An Instagram profile URL has no extra path segment: instagram.com/<handle>/
PROFILE_URL = re.compile(
    r"^https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]{1,30})/?(?:\?|$)"
)
RESERVED_PATHS = {"p", "reel", "reels", "tv", "explore", "stories", "accounts"}

BLOCK_MARKERS = ("/sorry/", "captcha-form", "unusual traffic", "trafego incomum")

WHITESPACE = re.compile(r"\s+")

# Below this length the text is a breadcrumb or a label, not a snippet.
MIN_SNIPPET = 20


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


def parse_results(page_html: str) -> list[SearchResult]:
    """Extract the organic results from a Google results page.

    Google's class names are obfuscated and rotate, so the extraction is
    structural instead: the h3 lives inside the result anchor, and the snippet
    lives outside it, in a sibling.
    """
    if not page_html:
        return []

    document = lxml_html.fromstring(page_html)
    results: list[SearchResult] = []
    seen: set[str] = set()

    for title in document.iter("h3"):
        anchor = find_anchor(title)
        if anchor is None:
            continue

        url = clean_url(anchor.get("href", ""))
        if not url or url in seen:
            continue

        seen.add(url)
        results.append(
            SearchResult(
                title=normalize(title.text_content()),
                url=url,
                snippet=find_snippet(anchor),
            )
        )

    return results


def is_blocked(url: str, page_html: str) -> bool:
    """Tell a block page from a page that simply had no results.

    Without this, a block looks exactly like a broken parser: zero results and
    no error.
    """
    haystack = f"{url} {page_html}".lower()
    return any(marker in haystack for marker in BLOCK_MARKERS)


def instagram_handle(url: str) -> str | None:
    """Return the handle of an Instagram profile URL, or None for anything else."""
    match = PROFILE_URL.match(url)
    if not match:
        return None
    handle = match.group(1).lower()
    return None if handle in RESERVED_PATHS else handle


def find_anchor(title):
    """Climb from the h3 to the anchor that wraps it."""
    node = title
    for _ in range(8):
        node = node.getparent()
        if node is None:
            return None
        if node.tag == "a" and node.get("href"):
            return node
    return None


def find_snippet(anchor) -> str:
    """Text in the result block that does not belong to the title anchor."""
    node = anchor
    for _ in range(6):
        node = node.getparent()
        if node is None:
            return ""
        # More than one h3 means we climbed past this result's own block, so the
        # text here belongs to a neighbouring result.
        if len(node.findall(".//h3")) > 1:
            return ""
        text = text_excluding(node, anchor)
        if len(text) >= MIN_SNIPPET:
            return text
    return ""


def text_excluding(container, anchor) -> str:
    """Join the container's text, skipping the anchor's subtree.

    Do not identify elements by id(): lxml builds proxies on demand and reuses
    id() once a proxy is collected. Ancestry is the reliable check.
    """
    parts: list[str] = []

    for element in container.iter():
        inside = element is anchor or anchor in element.iterancestors()
        if not inside and element.text:
            parts.append(element.text)
        # In lxml, tail belongs to the parent, so the anchor's own tail is
        # container text and counts.
        if element.tail and (not inside or element is anchor):
            parts.append(element.tail)

    return normalize(" ".join(parts))


def clean_url(href: str) -> str:
    """Resolve Google's /url?q= wrapper. Empty string for unusable hrefs."""
    href = href.strip()
    if not href.startswith(("http://", "https://", "/url?")):
        return ""

    if href.startswith("/url?"):
        target = parse_qs(urlparse(href).query).get("q", [""])[0]
        if not target.startswith(("http://", "https://")):
            return ""
        return target

    return href


def normalize(text: str) -> str:
    return WHITESPACE.sub(" ", text).strip()
