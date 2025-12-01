import paho.mqtt.client as mqtt
from .callbacks import connect_callback, on_subscribe, on_message
class MQTTClientConnection:

    def __init__(self, mqtt_broker_configs):
        self._ip_address = mqtt_broker_configs["HOST"]
        self._port = mqtt_broker_configs["PORT"]
        self._client_name = mqtt_broker_configs["CLIENT_NAME"]
        self._keepalive = mqtt_broker_configs["KEEPALIVE"]
    

    def start_connection(self) -> mqtt.Client:
        # Forçar protocolo MQTT v3.1.1 para compatibilidade com callbacks
        client = mqtt.Client(client_id=self._client_name, protocol=mqtt.MQTTv311)
        client.on_subscribe = on_subscribe
        client.on_connect = connect_callback
        client.on_message = on_message
        client.connect(self._ip_address, self._port, self._keepalive)
        client.loop_start()
        self._client = client
        return client
