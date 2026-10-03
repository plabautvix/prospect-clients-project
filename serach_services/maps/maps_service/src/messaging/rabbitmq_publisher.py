import json
import logging

import pika

from config.settings import settings

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """Singleton RabbitMQ publisher with automatic reconnection."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connection = None
            cls._instance._channel = None
        return cls._instance

    def _connect(self):
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
        )
        params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            # A BlockingConnection only answers heartbeats while the caller is
            # inside pika. This publisher sits idle for minutes between
            # scraping batches, so the broker would drop it for missing them.
            heartbeat=0,
            blocked_connection_timeout=300,
        )
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=settings.RABBITMQ_EXCHANGE,
            exchange_type="direct",
            durable=True,
        )
        self._channel.queue_declare(queue=settings.RABBITMQ_ROUTING_KEY, durable=True)
        self._channel.queue_bind(
            queue=settings.RABBITMQ_ROUTING_KEY,
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key=settings.RABBITMQ_ROUTING_KEY,
        )
        logger.info("RabbitMQ connected: %s:%s", settings.RABBITMQ_HOST, settings.RABBITMQ_PORT)

    def _ensure_connected(self):
        if self._connection is None or self._connection.is_closed:
            self._connect()
        if self._channel is None or self._channel.is_closed:
            self._channel = self._connection.channel()

    def publish(self, message: dict, retry: bool = True):
        """Publish one message, reconnecting once if the connection went stale.

        `is_closed` is not enough to trust a long-lived connection: pika only
        notices a dropped socket when it writes to it, so _ensure_connected
        passes and basic_publish is what raises. Without this retry, the first
        batch after an idle stretch is lost every time.
        """
        try:
            self._ensure_connected()
            self._channel.basic_publish(
                exchange=settings.RABBITMQ_EXCHANGE,
                routing_key=settings.RABBITMQ_ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except (pika.exceptions.AMQPError, OSError) as error:
            if not retry:
                raise
            logger.warning("RabbitMQ connection was stale (%s), reconnecting", error)
            self._discard_connection()
            self.publish(message, retry=False)
            return

        logger.info("Message published to RabbitMQ: %s", settings.RABBITMQ_EXCHANGE)

    def _discard_connection(self):
        """Throw away a connection that is already broken."""
        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except Exception:
            # Closing a dead connection raises, and there is nothing to
            # salvage: it is being replaced either way.
            pass
        finally:
            self._connection = None
            self._channel = None

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("RabbitMQ connection closed")
