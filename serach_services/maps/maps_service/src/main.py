from maps_service.src.configs.broker_configs import mqtt_broker_configs
from maps_service.src.maps_service.client_connection import MQTTClientConnection


# Mensageria, seria qualquer forma de comunicação entre softwares utilizando um broker. (Só para não esquecer)

def main():


    client = MQTTClientConnection(mqtt_broker_configs).start_connection()



if __name__ == "__main__":
    main()
