#!/usr/bin/env python
"""Run one query against Google and print the Instagram profiles it found.

    python scripts/probe.py 'site:instagram.com "veterinaria" Campinas'
    python scripts/probe.py '...' --pages 3
    python scripts/probe.py '...' --dump      # save the HTML of the last page
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from search import Blocked, GoogleSearch  # noqa: E402


async def run(args) -> int:
    search = GoogleSearch(headless=args.headless)
    await search.start()
    try:
        profiles = await search.find_profiles(args.query, pages=args.pages)
    except Blocked as error:
        print(f"blocked by Google: {error}")
        return 2
    finally:
        if args.dump and search.last_html:
            Path("dumps").mkdir(exist_ok=True)
            Path("dumps/last.html").write_text(search.last_html, encoding="utf-8")
            print("HTML saved to dumps/last.html")
        await search.stop()

    for handle, result in profiles.items():
        print(f"@{handle}")
        print(f"   {result.title}")
        print(f"   {result.snippet[:160]}")

    print(f"\n{len(profiles)} profiles in {search.queries} queries")
    return 0 if profiles else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="the search expression, quoted")
    parser.add_argument("--pages", type=int, default=3)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--dump", action="store_true", help="save the last page HTML")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
