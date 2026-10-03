"""Entry point: listens for operations on MQTT and runs the searches.

Payload published by the backend on `prospect/instagram`:

    {"status": 1, "id_operation": 42, "user_id": 7, "search_text": "...",
     "limit": 100}
    {"status": 0, "id_operation": 42}

No secret travels in the payload. The service authenticates to the backend with
its own X-Service-Key.
"""

import json
import logging

import paho.mqtt.client as mqtt

import config
from operations import Operations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

operations = Operations()


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        logger.error("MQTT connection failed: %s", reason_code)
        return
    client.subscribe(config.MQTT_TOPIC)
    logger.info("connected, subscribed to %s", config.MQTT_TOPIC)


def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode())
    logger.info("received: %s", payload)

    operation_id = payload["id_operation"]
    if payload["status"] == 1:
        operations.start(
            operation_id=operation_id,
            user_id=payload["user_id"],
            search_text=payload["search_text"],
            limit=payload.get("limit"),
        )
    else:
        operations.stop(operation_id)


def build_client() -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="instagram_service",
        protocol=mqtt.MQTTv311,
    )
    client.on_connect = on_connect
    client.on_message = on_message

    if config.MQTT_USERNAME:
        client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)

    return client


def main():
    logger.info("instagram service starting")
    client = build_client()
    client.connect(config.MQTT_HOST, config.MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
