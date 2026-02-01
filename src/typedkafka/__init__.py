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
from typedkafka.dlq import DeadLetterQueue, process_with_dlq
from typedkafka.exceptions import (
    ConsumerError,
    KafkaError,
    ProducerError,
    SerializationError,
)
from typedkafka.metrics import KafkaMetrics, KafkaStats
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

__version__ = "0.5.0"
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
    "KafkaMetrics",
    "KafkaStats",
    "DeadLetterQueue",
    "process_with_dlq",
    "testing",
]
