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

# Instagram puts the handle in the result title: "Nome (@handle) ...".
# This is more reliable than the href, which Google wraps in an opaque
# /goto?url=<blob> redirect that carries no readable URL.
TITLE_HANDLE = re.compile(r"\(@([A-Za-z0-9._]{1,30})\)")

# Checked against the final URL only. A real results page mentions /sorry/
# inside its scripts, so looking for these in the body matches every page.
BLOCK_URL_MARKERS = ("/sorry/", "/httpservice/retry")

# Checked against the body, but only when the page carries no results at all:
# a genuine results page can contain any phrase in a snippet.
BLOCK_TEXT_MARKERS = (
    "unusual traffic",
    "trafego incomum",
    "tráfego incomum",
    "captcha-form",
)

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

    for heading in document.iter("h3"):
        anchor = find_anchor(heading)
        if anchor is None:
            continue

        title = normalize(heading.text_content())
        if not title:
            continue

        # The URL may come back empty: Google wraps result links in an opaque
        # /goto?url=<blob> redirect. The result is kept anyway, because the
        # title still carries the handle.
        url = clean_url(anchor.get("href", ""))

        key = url or title
        if key in seen:
            continue
        seen.add(key)

        results.append(
            SearchResult(title=title, url=url, snippet=find_snippet(anchor))
        )

    return results


def is_blocked(url: str, page_html: str) -> bool:
    """Tell a block page from a page that simply had no results.

    Without this, a block looks exactly like a broken parser: zero results and
    no error.

    The two marker sets are checked differently on purpose. A real results page
    is hundreds of kilobytes of markup that mentions /sorry/ in its scripts, so
    body text alone cannot decide this. A block page, on the other hand, never
    carries result titles.
    """
    lowered_url = (url or "").lower()
    if any(marker in lowered_url for marker in BLOCK_URL_MARKERS):
        return True

    body = (page_html or "").lower()
    if not body:
        return True
    if "<h3" in body:
        return False
    return any(marker in body for marker in BLOCK_TEXT_MARKERS)


def instagram_handle(result: SearchResult) -> str | None:
    """Return the Instagram handle of a result, or None if it is not a profile.

    The URL is tried first, then the title. Google no longer exposes the target
    URL on result anchors: it wraps them in /goto?url=<opaque blob>, so on a
    live page the title is usually the only readable source.
    """
    return handle_from_url(result.url) or handle_from_title(result.title)


def handle_from_url(url: str) -> str | None:
    match = PROFILE_URL.match(url or "")
    if not match:
        return None
    handle = match.group(1).lower()
    return None if handle in RESERVED_PATHS else handle


def handle_from_title(title: str) -> str | None:
    match = TITLE_HANDLE.search(title or "")
    if not match:
        return None
    handle = match.group(1).lower()
    return None if handle in RESERVED_PATHS else handle


def profile_url(handle: str) -> str:
    """Canonical profile URL, rebuilt from the handle.

    Rebuilding beats carrying Google's redirect around: the stored lead gets a
    URL that works, and nothing downstream depends on Google's link format.
    """
    return f"https://www.instagram.com/{handle}/"


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
