"""Google search driven by a real Chrome instance through nodriver."""

import asyncio
import logging
from urllib.parse import urlencode

import nodriver as uc

import config
from serp import (
    SearchResult,
    instagram_handle,
    is_blocked,
    parse_results,
    profile_url,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.google.com/search"


class Blocked(Exception):
    """Google served a block page instead of results."""


class GoogleSearch:
    """One Chrome instance, reused across every query of an operation.

    Opening and closing a browser per query is slow and is itself a sign of
    automation, so the instance is long lived.
    """

    def __init__(
        self,
        headless: bool = config.HEADLESS,
        profile_dir: str = config.CHROME_PROFILE_DIR,
        delay: float = config.SEARCH_DELAY,
    ):
        self.headless = headless
        self.profile_dir = profile_dir
        self.delay = delay
        self.browser = None
        self.queries = 0
        self.last_html = ""

    async def start(self) -> None:
        options = {
            "headless": self.headless,
            "browser_args": [
                "--lang=pt-BR",
                "--disable-blink-features=AutomationControlled",
            ],
        }
        if self.profile_dir:
            options["user_data_dir"] = self.profile_dir
        self.browser = await uc.start(**options)

    async def stop(self) -> None:
        if self.browser:
            self.browser.stop()
            self.browser = None

    async def search(self, query: str, page: int = 0) -> list[SearchResult]:
        """Run one query and return its organic results."""
        if self.queries:
            await asyncio.sleep(self.delay)
        self.queries += 1

        tab = await self.browser.get(self.build_url(query, page))
        await asyncio.sleep(2)
        self.last_html = await tab.get_content()

        if is_blocked(tab.url, self.last_html):
            raise Blocked(tab.url)

        results = parse_results(self.last_html)
        logger.info("%d results for %r (page %d)", len(results), query, page)
        return results

    async def find_profiles(
        self,
        query: str,
        pages: int = config.MAX_PAGES,
        should_stop=None,
    ) -> dict[str, SearchResult]:
        """Search across pages and keep only Instagram profiles, by handle.

        `should_stop` is an optional callable checked between pages, so a running
        operation can be cancelled without this module knowing about threads.
        """
        profiles: dict[str, SearchResult] = {}

        for page in range(pages):
            if should_stop and should_stop():
                break
            results = await self.search(query, page)
            if not results:
                break
            for result in results:
                handle = instagram_handle(result)
                if handle and handle not in profiles:
                    # The stored URL is rebuilt from the handle, because the one
                    # on the page is Google's /goto redirect and does not work
                    # outside a search session.
                    profiles[handle] = SearchResult(
                        title=result.title,
                        url=profile_url(handle),
                        snippet=result.snippet,
                    )

        return profiles

    def build_url(self, query: str, page: int) -> str:
        # pws=0 turns off personalisation and filter=0 stops Google from hiding
        # results it considers similar. Both help recall.
        params = {
            "q": query,
            "hl": "pt-BR",
            "gl": "br",
            "pws": "0",
            "filter": "0",
        }
        if page:
            params["start"] = page * 10
        return f"{BASE_URL}?{urlencode(params)}"
