import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # MQTT
        self.MQTT_HOST: str = os.getenv("MQTT_HOST", "localhost")
        self.MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
        self.MQTT_CLIENT_NAME: str = os.getenv("MQTT_CLIENT_NAME", "maps_service_client")
        self.MQTT_KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
        self.MQTT_TOPIC: str = os.getenv("MQTT_TOPIC", "prospect/maps")

        # RabbitMQ
        self.RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
        self.RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
        self.RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.RABBITMQ_EXCHANGE: str = os.getenv("RABBITMQ_EXCHANGE", "fila_mensagens")
        self.RABBITMQ_ROUTING_KEY: str = os.getenv("RABBITMQ_ROUTING_KEY", "enviar")

        # Backend API
        self.BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")

        # Firefox / Selenium
        self.FIREFOX_BINARY_PATH: str = os.getenv("FIREFOX_BINARY_PATH", "")
        self.SELENIUM_HEADLESS: bool = os.getenv("SELENIUM_HEADLESS", "false").lower() == "true"


settings = Settings()
