import time
from client_mqtt.configs.broker_configs import mqtt_broker_configs
from client_mqtt.client_connection import MQTTClientConnection

# Mensageria seria a tecnica de enviar mensagens entre sistemas distribuídos.
def main():
    MQTTClientConnection(mqtt_broker_configs).start_connection()

if __name__ == "__main__":
    main()
    while True: time.sleep(0.001)  # Mantém o script rodando