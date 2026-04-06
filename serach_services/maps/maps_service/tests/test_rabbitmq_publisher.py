from unittest.mock import patch, MagicMock

from messaging.rabbitmq_publisher import RabbitMQPublisher


class TestRabbitMQPublisher:
    def setup_method(self):
        # Reset singleton between tests
        RabbitMQPublisher._instance = None

    @patch("messaging.rabbitmq_publisher.pika")
    def test_publish_connects_and_sends(self, mock_pika):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False
        mock_channel.is_closed = False
        mock_pika.BlockingConnection.return_value = mock_connection

        publisher = RabbitMQPublisher()
        publisher.publish({"key": "value"})

        mock_pika.BlockingConnection.assert_called_once()
        mock_channel.basic_publish.assert_called_once()

    @patch("messaging.rabbitmq_publisher.pika")
    def test_singleton_returns_same_instance(self, mock_pika):
        a = RabbitMQPublisher()
        b = RabbitMQPublisher()
        assert a is b

    @patch("messaging.rabbitmq_publisher.pika")
    def test_reconnects_when_connection_closed(self, mock_pika):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_channel.is_closed = False
        mock_pika.BlockingConnection.return_value = mock_connection

        publisher = RabbitMQPublisher()

        # First call: connection is None, triggers connect
        mock_connection.is_closed = False
        publisher.publish({"msg": 1})
        assert mock_pika.BlockingConnection.call_count == 1

        # Simulate closed connection
        mock_connection.is_closed = True
        publisher.publish({"msg": 2})
        assert mock_pika.BlockingConnection.call_count == 2

    @patch("messaging.rabbitmq_publisher.pika")
    def test_close(self, mock_pika):
        mock_connection = MagicMock()
        mock_connection.is_closed = False
        mock_connection.channel.return_value = MagicMock(is_closed=False)
        mock_pika.BlockingConnection.return_value = mock_connection

        publisher = RabbitMQPublisher()
        publisher.publish({"test": True})
        publisher.close()

        mock_connection.close.assert_called_once()
