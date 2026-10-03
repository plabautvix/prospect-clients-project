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
        self.MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
        self.MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")

        # Backend API
        self.BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        # Service-to-service credential used to call the backend (X-Service-Key).
        self.SERVICE_API_KEY: str = os.getenv("SERVICE_API_KEY", "dev-service-key-change-me")

        # Firefox / Selenium
        self.FIREFOX_BINARY_PATH: str = os.getenv("FIREFOX_BINARY_PATH", "")
        self.SELENIUM_HEADLESS: bool = os.getenv("SELENIUM_HEADLESS", "false").lower() == "true"


settings = Settings()
