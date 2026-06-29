import logging

import requests

from config.settings import settings
from messaging.rabbitmq_publisher import RabbitMQPublisher
from scraper.lead_parser import build_lead_messages

logger = logging.getLogger(__name__)


class LeadService:
    def __init__(self, user_id: int, message_template: str):
        self._user_id = user_id
        self._message_template = message_template
        self._publisher = RabbitMQPublisher()

    def process_found_leads(self, leads: list[dict]):
        self._send_leads_to_api(leads)
        messages = build_lead_messages(leads, self._message_template)
        if messages:
            self._publish_to_rabbitmq(messages)

    def _send_leads_to_api(self, leads: list[dict]):
        url = f"{settings.BACKEND_API_URL}/leads/"
        headers = {
            "X-Service-Key": settings.SERVICE_API_KEY,
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                url, json=leads, params={"user_id": self._user_id}, headers=headers
            )
            if response.status_code == 201:
                logger.info("Leads inserted successfully (%d leads)", len(leads))
            else:
                logger.warning("Failed to insert leads: %s %s", response.status_code, response.text)
        except requests.RequestException:
            logger.exception("Error sending leads to backend API")

    def _publish_to_rabbitmq(self, messages: list[dict]):
        try:
            self._publisher.publish({"messages": messages})
            logger.info("Published %d messages to RabbitMQ", len(messages))
        except Exception:
            logger.exception("Error publishing to RabbitMQ")
