"""Runs one search operation per thread.

Same shape as maps_service: the MQTT callback must return immediately, so the
work goes to a daemon thread with a stop event. Running operations live in
memory only; the backend reconciles orphans on startup.
"""

import asyncio
import logging
import threading

import backend
from search import GoogleSearch

logger = logging.getLogger(__name__)

# leads.categoria is String(100).
CATEGORY_LIMIT = 100


class Operations:
    def __init__(self):
        self._running: dict[int, threading.Event] = {}
        self._lock = threading.Lock()

    def start(self, operation_id: int, user_id: int, search_text: str) -> None:
        stop_event = threading.Event()

        with self._lock:
            if operation_id in self._running:
                logger.warning("operation %d is already running", operation_id)
                return
            if self._running:
                # Every operation drives the same Chrome profile, so a second
                # browser would fight the first one over it.
                logger.warning(
                    "operation %d refused: %s already running",
                    operation_id,
                    sorted(self._running),
                )
                backend.update_operation_status(operation_id, status=0)
                return
            self._running[operation_id] = stop_event

        threading.Thread(
            target=self._run,
            args=(operation_id, user_id, search_text, stop_event),
            name=f"ig-search-{operation_id}",
            daemon=True,
        ).start()

        logger.info("operation %d started: %s", operation_id, search_text)

    def stop(self, operation_id: int) -> None:
        with self._lock:
            stop_event = self._running.get(operation_id)

        if stop_event is None:
            logger.warning("operation %d is not running here", operation_id)
        else:
            stop_event.set()
            logger.info("operation %d asked to stop", operation_id)

        # The backend is updated either way, so a restarted service cannot
        # leave an operation marked active forever.
        self._mark_stopped(operation_id)

    def _run(self, operation_id, user_id, search_text, stop_event) -> None:
        # nodriver is async, so each operation thread gets its own event loop.
        try:
            asyncio.run(
                self._search(operation_id, user_id, search_text, stop_event)
            )
        finally:
            with self._lock:
                self._running.pop(operation_id, None)
            self._mark_stopped(operation_id)
            logger.info("operation %d finished", operation_id)

    async def _search(self, operation_id, user_id, search_text, stop_event) -> None:
        search = GoogleSearch()
        await search.start()
        try:
            profiles = await search.find_profiles(
                build_query(search_text), should_stop=stop_event.is_set
            )
        finally:
            await search.stop()

        if not profiles:
            logger.info("no profiles found for %r", search_text)
            return

        backend.post_leads(to_leads(profiles, search_text), user_id, operation_id)

    def _mark_stopped(self, operation_id: int) -> None:
        # Best effort: if the backend is down, the operation stays active in the
        # UI, and that is better than killing the thread on the way out.
        try:
            backend.update_operation_status(operation_id, status=0)
        except Exception:
            logger.exception("could not mark operation %d as stopped", operation_id)


def build_query(search_text: str) -> str:
    """Turn what the user typed in the frontend into a Google query."""
    return f"site:instagram.com {search_text}"


def to_leads(profiles: dict, search_text: str) -> list[dict]:
    """Map profiles onto the existing lead schema.

    The handle goes in `nome` because it is unique on Instagram and `leads.nome`
    is the upsert key. `categoria` carries the search text, which the frontend
    already exposes as a filter.
    """
    return [
        {
            "nome": f"@{handle}",
            "site": result.url,
            "categoria": search_text[:CATEGORY_LIMIT],
            "origem": "instagram",
        }
        for handle, result in profiles.items()
    ]
