import logging

import paho.mqtt.client as mqtt

from config.settings import settings
from messaging.mqtt_handler import on_connect, on_subscribe, on_message

logger = logging.getLogger(__name__)


def create_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(
        client_id=settings.MQTT_CLIENT_NAME, protocol=mqtt.MQTTv311
    )
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    client.connect(settings.MQTT_HOST, settings.MQTT_PORT, settings.MQTT_KEEPALIVE)
    logger.info("MQTT client connecting to %s:%s", settings.MQTT_HOST, settings.MQTT_PORT)
    return client


def run_mqtt():
    client = create_mqtt_client()
    logger.info("MQTT client started, entering loop_forever()")
    client.loop_forever()
