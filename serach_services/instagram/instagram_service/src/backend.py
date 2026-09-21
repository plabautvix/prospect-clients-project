"""Calls to the backend API, authenticated with the service key.

The service never touches the database. Every write goes through the backend
with the X-Service-Key header, same as maps_service.
"""

import logging

import requests

import config

logger = logging.getLogger(__name__)

TIMEOUT = 30
HEADERS = {"X-Service-Key": config.SERVICE_API_KEY}


def post_leads(
    leads: list[dict], user_id: int, operation_id: int | None = None
) -> None:
    response = requests.post(
        f"{config.BACKEND_API_URL}/leads/",
        json=leads,
        params={"user_id": user_id, "operation_id": operation_id},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    logger.info("posted %d leads for user %d", len(leads), user_id)


def update_operation_status(operation_id: int, status: int) -> None:
    response = requests.patch(
        f"{config.BACKEND_API_URL}/operations/{operation_id}/status",
        json={"status": status},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    logger.info("operation %d status set to %d", operation_id, status)
