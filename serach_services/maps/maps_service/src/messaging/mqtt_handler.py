import json
import logging

from services.operation_service import OperationService

logger = logging.getLogger(__name__)

_operation_service = OperationService()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        from config.settings import settings
        client.subscribe(settings.MQTT_TOPIC)
        logger.info("Connected to MQTT broker, subscribed to %s", settings.MQTT_TOPIC)
        return
    logger.error("MQTT connection failed with code %s", rc)


def on_subscribe(client, userdata, mid, granted_qos):
    logger.info("MQTT subscription confirmed. MID: %s, QoS: %s", mid, granted_qos)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.info("MQTT message received: %s", payload)

        status = payload.get("status")

        if status == 1:
            _operation_service.start_operation(
                search_text=payload.get("search_text"),
                message_text=payload.get("message_user"),
                user_id=payload.get("user_id"),
                title=payload.get("title"),
                operation_id=payload.get("id_operation"),
            )
        else:
            _operation_service.stop_operation(
                operation_id=payload.get("id_operation"),
            )
    except Exception:
        logger.exception("Error processing MQTT message")
