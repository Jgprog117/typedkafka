"""
typedkafka - A well-documented, fully type-hinted Kafka client for Python.

Built on confluent-kafka with comprehensive docstrings, full type hints,
and a modern Pythonic API.
"""

from typedkafka.admin import KafkaAdmin, AdminError, TopicConfig
from typedkafka.config import ProducerConfig, ConsumerConfig
from typedkafka.consumer import KafkaConsumer
from typedkafka.exceptions import (
    ConsumerError,
    KafkaError,
    ProducerError,
    SerializationError,
)
from typedkafka.producer import KafkaProducer

# Testing utilities in separate namespace
from typedkafka import testing

__version__ = "0.2.0"  # Bumped for new features
__all__ = [
    "KafkaProducer",
    "KafkaConsumer",
    "KafkaAdmin",
    "ProducerConfig",
    "ConsumerConfig",
    "TopicConfig",
    "KafkaError",
    "ProducerError",
    "ConsumerError",
    "SerializationError",
    "AdminError",
    "testing",
]
