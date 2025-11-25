import paho.mqtt.client as mqtt


class MQTTClientConnection:

    def __init__(self, mqtt_broker_configs):
        self._ip_address = mqtt_broker_configs["HOST"]
        self._port = mqtt_broker_configs["PORT"]
        self._client_name = mqtt_broker_configs["CLIENT_NAME"]
        self._keepalive = mqtt_broker_configs["KEEPALIVE"]
    

    def start_connection(self) -> mqtt.Client:
        client = mqtt.Client(self._client_name)
        client.connect(self._ip_address, self._port, self._keepalive)
        client.loop_start()
        self._client = client
        return client
    