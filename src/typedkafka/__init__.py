"""
typedkafka - A well-documented, fully type-hinted Kafka client for Python.

Built on confluent-kafka with comprehensive docstrings, full type hints,
and a modern Pythonic API.
"""

# Testing utilities in separate namespace
from typedkafka import testing
from typedkafka.admin import AdminError, KafkaAdmin, TopicConfig
from typedkafka.config import ConsumerConfig, ProducerConfig
from typedkafka.consumer import KafkaConsumer, KafkaMessage
from typedkafka.exceptions import (
    ConsumerError,
    KafkaError,
    ProducerError,
    SerializationError,
)
from typedkafka.producer import KafkaProducer, TransactionContext
from typedkafka.retry import RetryPolicy, retry
from typedkafka.serializers import (
    Deserializer,
    JsonDeserializer,
    JsonSerializer,
    Serializer,
    StringDeserializer,
    StringSerializer,
)

__version__ = "0.3.3"
__all__ = [
    "KafkaProducer",
    "KafkaConsumer",
    "KafkaMessage",
    "KafkaAdmin",
    "ProducerConfig",
    "ConsumerConfig",
    "TopicConfig",
    "KafkaError",
    "ProducerError",
    "ConsumerError",
    "SerializationError",
    "AdminError",
    "TransactionContext",
    "retry",
    "RetryPolicy",
    "Serializer",
    "Deserializer",
    "JsonSerializer",
    "JsonDeserializer",
    "StringSerializer",
    "StringDeserializer",
    "testing",
]
