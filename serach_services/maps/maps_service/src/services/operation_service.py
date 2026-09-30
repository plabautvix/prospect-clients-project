import logging
import threading

import requests

from config.settings import settings
from scraper.maps_scraper import scrape_maps
from services.lead_service import LeadService

logger = logging.getLogger(__name__)


class OperationService:
    def __init__(self):
        self._active_operations: dict[int, dict] = {}
        self._lock = threading.Lock()

    def start_operation(
        self, search_text: str, message_text: str, user_id: int,
        operation_id: int | None = None, title: str | None = None,
        limit: int | None = None,
    ):
        # The operation is always created by the backend, which sends its id here.
        if operation_id is None:
            logger.error("No operation_id provided, aborting")
            return

        stop_event = threading.Event()
        lead_service = LeadService(
            user_id=user_id,
            message_template=message_text,
            operation_id=operation_id,
        )

        def _run_and_finalize():
            scrape_maps(
                search_text, stop_event, lead_service.process_found_leads,
                limit=limit,
            )
            with self._lock:
                self._active_operations.pop(operation_id, None)
            self._update_operation_status_via_api(operation_id, status=0)
            logger.info("Operation %s finished automatically", operation_id)

        thread = threading.Thread(
            target=_run_and_finalize,
            name=f"scraper-{operation_id}",
            daemon=True,
        )
        thread.start()

        with self._lock:
            self._active_operations[operation_id] = {
                "thread": thread,
                "stop_event": stop_event,
            }

        logger.info("Operation %s started: %s", operation_id, search_text)

    def stop_operation(self, operation_id: int):
        with self._lock:
            op = self._active_operations.pop(operation_id, None)

        if op is None:
            # The thread may not exist here (e.g. maps_service was restarted).
            # We still ensure the database is made consistent as stopped.
            logger.warning("Operation %s not found in active operations", operation_id)
        else:
            op["stop_event"].set()
            op["thread"].join(timeout=30)

        self._update_operation_status_via_api(operation_id, status=0)
        logger.info("Operation %s stopped", operation_id)

    def _update_operation_status_via_api(self, operation_id: int, status: int):
        url = f"{settings.BACKEND_API_URL}/operations/{operation_id}/status"
        headers = {
            "X-Service-Key": settings.SERVICE_API_KEY,
            "Content-Type": "application/json",
        }
        try:
            response = requests.patch(url, json={"status": status}, headers=headers)
            if response.status_code == 200:
                logger.info("Operation %s status updated to %s", operation_id, status)
            else:
                logger.warning("API returned %s: %s", response.status_code, response.text)
        except requests.RequestException:
            logger.exception("Error updating operation status via API")
