import sqlite3
import json
from client_mqtt.configs.broker_configs import mqtt_broker_configs


def connect_callback(client, userdata, flags, rc, properties=None):
    """
    Callback for when the client receives a CONNACK response from the server.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: The private user data as set in Client() or userdata_set().
        flags (dict): Response flags sent by the broker.
        rc (int): The connection result.
        properties: MQTT v5.0 properties (not used here).
    """
    if rc == 0:
        client.subscribe(mqtt_broker_configs["TOPIC"])
        return
    
    raise Exception(f"Falha na conexão com o broker MQTT. Código de retorno: {rc}")

def on_subscribe(client, userdata, mid, granted_qos):
    """
    Callback for when the client subscribes to a topic.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: The private user data as set in Client() or userdata_set().
        mid (int): Message ID for the subscribe request.
        granted_qos (list): List of granted QoS levels for each subscribed topic.
    """
    print(f"Inscrição realizada com sucesso. MID: {mid}, QoS concedido: {granted_qos}")


def on_message(client, userdata, msg):
    """
    Callback for when a PUBLISH message is received from the server.

    Args:
        client (mqtt.Client): The MQTT client instance.
        userdata: The private user data as set in Client() or userdata_set().
        msg (mqtt.MQTTMessage): An instance of MQTTMessage, which contains topic, payload, qos, retain.
    """

    conn = sqlite3.connect('C:\\Users\\Pedro\\Documents\\Prospect Clients\\prospect-clients-project\\back_end\\test.db')
    cursor = conn.cursor()

    message = msg.payload.decode()
    message_object = json.loads(message)

    if message_object.get("status") == 1:
        cursor.execute("""
            INSERT INTO operations (operation_name, status, search_text)
            VALUES (?, ?, ?)
        """, (message_object.get("title"), 1, message_object.get("search_text")))

        conn.commit()
        print("Operação de scraping iniciada e registrada no banco de dados.")
    else:
        cursor.execute("""
            UPDATE operations
            SET status = 0
            WHERE id_operation = ?
        """, (message_object.get("id_operation"),))

        conn.commit()
        print("Operação de scraping parada e atualizada no banco de dados.")
    print(type(message))


    print(f"Mensagem recebida no tópico {msg.topic}: {msg.payload.decode()}")