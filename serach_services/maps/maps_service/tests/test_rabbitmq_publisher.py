import pytest
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


class TestStaleConnection:
    """The publisher sits idle between scraping batches and gets dropped."""

    def setup_method(self):
        RabbitMQPublisher._instance = None

    @staticmethod
    def _mock_connection(mock_pika):
        connection = MagicMock()
        channel = MagicMock()
        connection.channel.return_value = channel
        connection.is_closed = False
        connection.is_open = True
        channel.is_closed = False
        mock_pika.BlockingConnection.return_value = connection
        return connection, channel

    @patch("messaging.rabbitmq_publisher.pika")
    def test_reconnects_and_resends_when_the_socket_died(self, mock_pika):
        # pika only notices a dropped socket when it writes, so is_closed stays
        # False and basic_publish is what raises.
        mock_pika.exceptions.AMQPError = RuntimeError
        connection, channel = self._mock_connection(mock_pika)
        channel.basic_publish.side_effect = [RuntimeError("stream lost"), None]

        RabbitMQPublisher().publish({"messages": ["a"]})

        assert channel.basic_publish.call_count == 2
        # A fresh connection, not the corpse of the old one.
        assert mock_pika.BlockingConnection.call_count == 2

    @patch("messaging.rabbitmq_publisher.pika")
    def test_gives_up_after_one_retry(self, mock_pika):
        mock_pika.exceptions.AMQPError = RuntimeError
        _, channel = self._mock_connection(mock_pika)
        channel.basic_publish.side_effect = RuntimeError("broker is down")

        with pytest.raises(RuntimeError):
            RabbitMQPublisher().publish({"messages": ["a"]})

        # Two attempts, not an endless loop.
        assert channel.basic_publish.call_count == 2

    @patch("messaging.rabbitmq_publisher.pika")
    def test_heartbeats_are_disabled(self, mock_pika):
        self._mock_connection(mock_pika)

        RabbitMQPublisher().publish({"messages": ["a"]})

        assert mock_pika.ConnectionParameters.call_args[1]["heartbeat"] == 0
