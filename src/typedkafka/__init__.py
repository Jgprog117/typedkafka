"""
typedkafka - A well-documented, fully type-hinted Kafka client for Python.

Built on confluent-kafka with comprehensive docstrings, full type hints,
and a modern Pythonic API.
"""

from typedkafka.consumer import KafkaConsumer
from typedkafka.exceptions import (
    ConsumerError,
    KafkaError,
    ProducerError,
    SerializationError,
)
from typedkafka.producer import KafkaProducer

__version__ = "0.1.0"
__all__ = [
    "KafkaProducer",
    "KafkaConsumer",
    "KafkaError",
    "ProducerError",
    "ConsumerError",
    "SerializationError",
]
