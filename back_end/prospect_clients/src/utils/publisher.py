import json
import logging
import os
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load back_end/.env so MQTT credentials work in local dev (no-op under Docker,
# where env vars come from the orchestrator and take precedence).
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

_host = os.getenv("MQTT_HOST", "localhost")
_port = int(os.getenv("MQTT_PORT", "1883"))
_username = os.getenv("MQTT_USERNAME")
_password = os.getenv("MQTT_PASSWORD")
_tls = os.getenv("MQTT_TLS", "false").lower() == "true"
_ca_cert = os.getenv("MQTT_CA_CERT")

mqtt_client = mqtt.Client()
if _username:
    mqtt_client.username_pw_set(_username, _password)
if _tls:
    # Validate the broker certificate against our CA.
    mqtt_client.tls_set(ca_certs=_ca_cert)


def _connect_with_retry(retries: int = 10, delay: float = 2.0):
    for attempt in range(1, retries + 1):
        try:
            mqtt_client.connect(_host, _port, 60)
            mqtt_client.loop_start()
            logger.info("MQTT connected to %s:%s", _host, _port)
            return
        except Exception as e:
            logger.warning("MQTT connect failed (%d/%d): %s", attempt, retries, e)
            time.sleep(delay)
    logger.error("MQTT connection failed after %d attempts", retries)


_connect_with_retry()


def publish_message(topic: str, message: object) -> None:
    result = mqtt_client.publish(topic, payload=json.dumps(message))
    result.wait_for_publish(timeout=5)
    logger.info("MQTT published to %s: %s", topic, message)