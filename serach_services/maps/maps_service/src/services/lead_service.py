import logging

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


class LeadService:
    def __init__(self, user_id: int, operation_id: int | None = None):
        self._user_id = user_id
        self._operation_id = operation_id

    def process_found_leads(self, leads: list[dict]):
        # Only stores them. Messages are sent through campaigns, which the
        # user creates and reviews from the leads screen.
        self._send_leads_to_api(leads)

    def _send_leads_to_api(self, leads: list[dict]):
        url = f"{settings.BACKEND_API_URL}/leads/"
        headers = {
            "X-Service-Key": settings.SERVICE_API_KEY,
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                url,
                json=leads,
                params={
                    "user_id": self._user_id,
                    "operation_id": self._operation_id,
                },
                headers=headers,
            )
            if response.status_code == 201:
                logger.info("Leads inserted successfully (%d leads)", len(leads))
            else:
                logger.warning("Failed to insert leads: %s %s", response.status_code, response.text)
        except requests.RequestException:
            logger.exception("Error sending leads to backend API")
