import json
import os
import paho.mqtt.client as mqtt

_host = os.getenv("MQTT_HOST", "localhost")
_port = int(os.getenv("MQTT_PORT", "1883"))

mqtt_client = mqtt.Client()
mqtt_client.connect(_host, _port, 60)


def publish_message(topic: str, message: object) -> None:
    mqtt_client.publish(topic, payload=json.dumps(message))
    return