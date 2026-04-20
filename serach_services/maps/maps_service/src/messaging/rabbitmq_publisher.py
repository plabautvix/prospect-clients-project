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

    def publish(self, message: dict):
        self._ensure_connected()
        self._channel.basic_publish(
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key=settings.RABBITMQ_ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        logger.info("Message published to RabbitMQ: %s", settings.RABBITMQ_EXCHANGE)

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("RabbitMQ connection closed")
