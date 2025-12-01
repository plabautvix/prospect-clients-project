import json
import paho.mqtt.client as mqtt

mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883, 60)


def publish_message(topic: str, message: object) -> None:
    mqtt_client.publish(topic, payload=json.dumps(message))
    return