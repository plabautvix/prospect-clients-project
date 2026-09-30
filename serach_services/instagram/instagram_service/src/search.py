"""Google search driven by a real Chrome instance through nodriver.

The interaction is deliberately shaped like a person's. The query is typed into
Google's own search box, the page is scrolled before being read, and further
pages are reached by clicking Next. Requesting /search?start=20 directly is the
clearest bot signal of the lot, and it is what got this service blocked: pages
one and two came back fine, the third was refused every time.
"""

import asyncio
import logging
import random
import subprocess
from pathlib import Path

import nodriver as uc
from nodriver import cdp

import config
from serp import (
    SearchResult,
    instagram_handle,
    is_blocked,
    parse_results,
    profile_url,
)

logger = logging.getLogger(__name__)

HOME_URL = "https://www.google.com/"
SEARCH_BOX = "textarea[name=q], input[name=q]"

# Google labels the next-page link differently depending on the layout it
# serves, so both the stable id and the visible text are worth trying.
NEXT_SELECTORS = ("a#pnnext", "a[aria-label*='Pr']", "a[aria-label*='Next']")
NEXT_TEXTS = ("Próxima", "Mais resultados", "Next", "More results")


class Blocked(Exception):
    """Google served a block page instead of results."""


def release_profile(profile_dir: str) -> None:
    """Make a persisted profile usable again after a run that ended badly.

    Two things can hold it. A Chrome that is still alive, left behind when a
    launch failed half way and stop() never ran; and the lock file, which
    Chrome never clears itself after an unclean exit. Both make every later run
    fail the same way, so one bad start would otherwise poison the volume.

    Only browsers opened on this exact profile are killed, so nothing else on
    the machine is touched. Assumes one browser per profile, which holds while
    one operation runs at a time.
    """
    subprocess.run(
        ["pkill", "-f", f"--user-data-dir={profile_dir}"],
        check=False,
        capture_output=True,
    )
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        Path(profile_dir, name).unlink(missing_ok=True)


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
        self.tab = None
        self.queries = 0
        self.last_html = ""

    async def start(self) -> None:
        options = {
            "headless": self.headless,
            "browser_args": [
                "--lang=pt-BR",
                "--disable-blink-features=AutomationControlled",
                # The container runs as root, and Chrome refuses to start as
                # root with its sandbox on.
                "--no-sandbox",
            ],
        }
        if self.profile_dir:
            release_profile(self.profile_dir)
            options["user_data_dir"] = self.profile_dir

        try:
            self.browser = await uc.start(**options)
        except Exception:
            # A launch that fails part way still leaves Chrome running and
            # holding the profile. Left alone it would break every later run.
            if self.profile_dir:
                release_profile(self.profile_dir)
            raise

    async def stop(self) -> None:
        if self.browser:
            self.browser.stop()
            self.browser = None
            self.tab = None

    async def find_profiles(
        self,
        query: str,
        pages: int = config.MAX_PAGES,
        should_stop=None,
        limit: int | None = None,
    ) -> dict[str, SearchResult]:
        """Search and keep only Instagram profiles, by handle.

        Goes as deep as Google allows. The run ends when there is no next page,
        when Google blocks, or when the caller asks it to stop. `pages` is only
        a ceiling for callers that want one; 0 means no ceiling.

        `should_stop` is an optional callable checked between pages, so a
        running operation can be cancelled without this module knowing about
        threads.
        """
        profiles: dict[str, SearchResult] = {}
        previous_titles: list[str] = []
        page = 0

        await self.open_search(query)

        while True:
            if pages and page >= pages:
                logger.info("stopping at the %d page ceiling", pages)
                break

            if should_stop and should_stop():
                break

            if page and not await self.go_to_next_page():
                logger.info("no next page after page %d", page - 1)
                break

            try:
                results = await self.read_results()
            except Blocked:
                # Keep what the earlier pages gave us. Google tends to block
                # part way through, and throwing away the pages that already
                # worked loses most of the run.
                logger.warning(
                    "blocked on page %d, keeping %d profiles found so far",
                    page,
                    len(profiles),
                )
                break

            if not results:
                break

            # Without a page ceiling, a next link that fails to navigate would
            # re-read the same page forever. Identical content means stuck.
            titles = [r.title for r in results]
            if titles == previous_titles:
                logger.warning(
                    "page %d repeated the previous one, stopping", page
                )
                break
            previous_titles = titles

            new = duplicates = 0
            for result in results:
                handle = instagram_handle(result)
                if not handle:
                    # This is the only way a result is silently dropped, so the
                    # log carries the breadcrumb too: "instagram.com > p >
                    # CODE" means a post and the drop is right, while
                    # "instagram.com > somename" means a profile was lost.
                    logger.warning(
                        "no handle on page %d | title=%r | cite=%r",
                        page,
                        result.title,
                        result.cite,
                    )
                    continue
                if handle in profiles:
                    duplicates += 1
                    continue
                new += 1
                # The stored URL is rebuilt from the handle, because the one on
                # the page is Google's /goto redirect and does not work outside
                # a search session.
                profiles[handle] = SearchResult(
                    title=result.title,
                    url=profile_url(handle),
                    snippet=result.snippet,
                    cite=result.cite,
                )
                if limit and len(profiles) >= limit:
                    break

            logger.info(
                "page %d: %d results, %d new, %d repeated, %d without handle",
                page,
                len(results),
                new,
                duplicates,
                len(results) - new - duplicates,
            )
            page += 1

            if limit and len(profiles) >= limit:
                logger.info("reached the requested limit of %d profiles", limit)
                break

        logger.info(
            "finished with %d profiles after %d pages", len(profiles), page
        )
        return profiles

    async def open_search(self, query: str) -> None:
        """Type the query into Google's own search box and submit it."""
        self.tab = await self.browser.get(HOME_URL)
        await self.pause(1.5, 3.0)

        box = await self.tab.select(SEARCH_BOX, timeout=15)
        await box.click()
        await self.pause(0.3, 0.8)
        await self.type_like_a_person(box, query)

        # Reading back what you typed before hitting enter.
        await self.pause(0.5, 1.4)
        await self.press_enter()
        await self.pause(2.0, 3.5)

        self.queries += 1

    async def read_results(self) -> list[SearchResult]:
        """Scroll the page the way a reader does, then parse what is there."""
        await self.skim_the_page()

        self.last_html = await self.tab.get_content()
        if is_blocked(self.tab.url, self.last_html):
            raise Blocked(self.tab.url)

        return parse_results(self.last_html)

    async def go_to_next_page(self) -> bool:
        """Click the next-page link. False when there is no next page."""
        link = await self.find_next_link()
        if link is None:
            return False

        await link.scroll_into_view()
        await self.pause(0.4, 1.1)
        await link.click()

        # Between pages a person takes noticeably longer than between scrolls,
        # and never the same amount twice.
        await self.pause(self.delay * 0.6, self.delay * 1.8)
        self.queries += 1
        return True

    async def find_next_link(self):
        for selector in NEXT_SELECTORS:
            try:
                return await self.tab.select(selector, timeout=2)
            except Exception:
                continue

        for text in NEXT_TEXTS:
            try:
                return await self.tab.find(text, best_match=True, timeout=2)
            except Exception:
                continue

        # No next link is a normal end of results, not a failure.
        return None

    async def skim_the_page(self) -> None:
        """Scroll down in a few uneven steps, pausing like someone reading."""
        for _ in range(random.randint(2, 4)):
            await self.tab.scroll_down(random.randint(20, 45))
            await self.pause(0.6, 1.8)

    async def type_like_a_person(self, box, query: str) -> None:
        """Type in short bursts instead of pasting the whole string at once."""
        for char in query:
            await box.send_keys(char)
            await asyncio.sleep(random.uniform(0.04, 0.17))
            # The occasional longer gap, as if thinking mid-phrase.
            if char == " " and random.random() < 0.3:
                await asyncio.sleep(random.uniform(0.2, 0.6))

    async def press_enter(self) -> None:
        """Press Enter as a real key press.

        send_keys only dispatches `char` events, which insert text but never
        submit a form, so typing "\\n" leaves you sitting on the homepage.
        A full keyDown/char/keyUp with the Enter key codes is what the page
        actually listens for.
        """
        for event_type in ("keyDown", "char", "keyUp"):
            await self.tab.send(
                cdp.input_.dispatch_key_event(
                    type_=event_type,
                    key="Enter",
                    code="Enter",
                    text="\r",
                    unmodified_text="\r",
                    windows_virtual_key_code=13,
                    native_virtual_key_code=13,
                )
            )

    async def pause(self, low: float, high: float) -> None:
        await asyncio.sleep(random.uniform(low, high))
