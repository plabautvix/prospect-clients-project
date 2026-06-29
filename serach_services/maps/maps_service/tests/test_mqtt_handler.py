import json
from unittest.mock import patch, MagicMock

from messaging.mqtt_handler import on_message, on_connect


class TestOnConnect:
    @patch("config.settings.settings")
    def test_on_connect_success_subscribes(self, mock_settings):
        mock_settings.MQTT_TOPIC = "test/topic"
        client = MagicMock()

        on_connect(client, None, None, 0)

        client.subscribe.assert_called_once_with("test/topic")

    def test_on_connect_failure_logs_error(self):
        client = MagicMock()
        # rc != 0 means failure — should not subscribe
        on_connect(client, None, None, 1)
        client.subscribe.assert_not_called()


class TestOnMessage:
    @patch("messaging.mqtt_handler._operation_service")
    def test_start_operation(self, mock_service):
        msg = MagicMock()
        msg.payload.decode.return_value = json.dumps({
            "status": 1,
            "id_operation": 7,
            "search_text": "padarias SP",
            "message_user": "Ola {nome}",
            "user_id": 1,
            "title": "Padarias",
        })

        on_message(None, None, msg)

        mock_service.start_operation.assert_called_once_with(
            search_text="padarias SP",
            message_text="Ola {nome}",
            user_id=1,
            title="Padarias",
            operation_id=7,
        )

    @patch("messaging.mqtt_handler._operation_service")
    def test_stop_operation(self, mock_service):
        msg = MagicMock()
        msg.payload.decode.return_value = json.dumps({
            "status": 0,
            "id_operation": 42,
        })

        on_message(None, None, msg)

        mock_service.stop_operation.assert_called_once_with(
            operation_id=42,
        )

    @patch("messaging.mqtt_handler._operation_service")
    def test_invalid_json_does_not_crash(self, mock_service):
        msg = MagicMock()
        msg.payload.decode.return_value = "not json {{"

        # Should not raise
        on_message(None, None, msg)

        mock_service.start_operation.assert_not_called()
        mock_service.stop_operation.assert_not_called()
