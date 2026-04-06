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
        self, search_text: str, message_text: str, token: str, user_id: int,
        title: str | None = None, operation_id: int | None = None,
    ):
        if operation_id is None:
            operation_id = self._create_operation_via_api(
                token=token,
                operation_name=title or search_text,
                search_text=search_text,
                message_for_lead=message_text,
            )
        if operation_id is None:
            logger.error("Failed to create operation via API, aborting")
            return

        stop_event = threading.Event()
        lead_service = LeadService(token=token, message_template=message_text)

        thread = threading.Thread(
            target=scrape_maps,
            args=(search_text, stop_event, lead_service.process_found_leads),
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

    def stop_operation(self, operation_id: int, token: str):
        with self._lock:
            op = self._active_operations.pop(operation_id, None)

        if op is None:
            logger.warning("Operation %s not found in active operations", operation_id)
            return

        op["stop_event"].set()
        op["thread"].join(timeout=30)

        self._update_operation_status_via_api(token, operation_id, status=0)
        logger.info("Operation %s stopped", operation_id)

    def _create_operation_via_api(
        self, token: str, operation_name: str, search_text: str,
        message_for_lead: str | None,
    ) -> int | None:
        url = f"{settings.BACKEND_API_URL}/operations/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "operation_name": operation_name,
            "search_text": search_text,
            "message_for_lead": message_for_lead,
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                op_id = response.json()["id_operation"]
                logger.info("Operation created via API: %s", op_id)
                return op_id
            logger.warning("API returned %s: %s", response.status_code, response.text)
        except requests.RequestException:
            logger.exception("Error creating operation via API")
        return None

    def _update_operation_status_via_api(
        self, token: str, operation_id: int, status: int
    ):
        url = f"{settings.BACKEND_API_URL}/operations/{operation_id}/status"
        headers = {
            "Authorization": f"Bearer {token}",
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
