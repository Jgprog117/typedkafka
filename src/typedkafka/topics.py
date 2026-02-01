"""
Type-safe topic bindings for compile-time type checking.

Provides ``TypedTopic[T]`` which binds a topic name to a serializer/deserializer
pair, enabling end-to-end type safety when producing and consuming messages.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from typedkafka.serializers import (
    Deserializer,
    JsonDeserializer,
    JsonSerializer,
    Serializer,
    StringDeserializer,
    StringSerializer,
)

T = TypeVar("T")


class TypedTopic(Generic[T]):
    """
    A type-safe topic that binds a topic name to serializer/deserializer pairs.

    Provides compile-time type safety when used with ``KafkaProducer.send_typed()``
    and ``KafkaMessage.decode()``. IDEs will autocomplete and type-check message
    values based on the topic's type parameter.

    Args:
        name: Kafka topic name.
        value_serializer: Serializer for message values.
        value_deserializer: Deserializer for message values.
        key_serializer: Optional serializer for message keys.
        key_deserializer: Optional deserializer for message keys.

    Examples:
        >>> from typedkafka.topics import TypedTopic, json_topic
        >>> from typedkafka.serializers import JsonSerializer, JsonDeserializer
        >>>
        >>> # Using factory function
        >>> events = json_topic("user-events")
        >>> producer.send_typed(events, {"user_id": 123})
        >>>
        >>> # Custom topic with explicit serializers
        >>> topic = TypedTopic(
        ...     "users",
        ...     value_serializer=JsonSerializer(),
        ...     value_deserializer=JsonDeserializer(),
        ... )
    """

    def __init__(
        self,
        name: str,
        value_serializer: Serializer[T],
        value_deserializer: Deserializer[T],
        key_serializer: Serializer[Any] | None = None,
        key_deserializer: Deserializer[Any] | None = None,
    ) -> None:
        self.name = name
        self.value_serializer = value_serializer
        self.value_deserializer = value_deserializer
        self.key_serializer = key_serializer
        self.key_deserializer = key_deserializer

    def __repr__(self) -> str:
        return f"TypedTopic(name={self.name!r})"


def json_topic(name: str) -> TypedTopic[Any]:
    """
    Create a TypedTopic for JSON messages.

    Args:
        name: Kafka topic name.

    Returns:
        A TypedTopic configured with JSON serialization.

    Examples:
        >>> events = json_topic("events")
        >>> producer.send_typed(events, {"user_id": 123})
    """
    return TypedTopic(
        name,
        value_serializer=JsonSerializer(),
        value_deserializer=JsonDeserializer(),
    )


def string_topic(name: str, encoding: str = "utf-8") -> TypedTopic[str]:
    """
    Create a TypedTopic for string messages.

    Args:
        name: Kafka topic name.
        encoding: Character encoding (default: utf-8).

    Returns:
        A TypedTopic configured with string serialization.

    Examples:
        >>> logs = string_topic("logs")
        >>> producer.send_typed(logs, "Application started")
    """
    return TypedTopic(
        name,
        value_serializer=StringSerializer(encoding),
        value_deserializer=StringDeserializer(encoding),
    )
