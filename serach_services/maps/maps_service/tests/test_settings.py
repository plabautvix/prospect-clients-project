import os
from unittest.mock import patch


class TestSettings:
    def test_default_values(self):
        from config.settings import Settings

        s = Settings()
        assert s.MQTT_HOST == "localhost"
        assert s.MQTT_PORT == 1883
        assert s.RABBITMQ_USER == "guest"
        assert s.BACKEND_API_URL == "http://localhost:8000"

    def test_env_override(self):
        with patch.dict(os.environ, {"MQTT_HOST": "broker.prod.com", "MQTT_PORT": "9999"}):
            from config.settings import Settings
            s = Settings()  # Reads os.getenv at init time
            assert s.MQTT_HOST == "broker.prod.com"
            assert s.MQTT_PORT == 9999

    def test_firefox_path_default_empty(self):
        from config.settings import Settings

        s = Settings()
        assert s.FIREFOX_BINARY_PATH == ""
