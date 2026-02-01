"""Protobuf serialization support for typedkafka.

Requires: ``pip install typedkafka[protobuf]``

Provides serializers and deserializers for Protocol Buffer messages,
with optional Schema Registry integration.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from typedkafka.exceptions import SerializationError
from typedkafka.serializers import Deserializer, Serializer

try:
    from google.protobuf.message import Message as ProtoMessage

    _PROTOBUF_AVAILABLE = True
except ImportError:
    ProtoMessage = None  # type: ignore[assignment,misc]
    _PROTOBUF_AVAILABLE = False

T = TypeVar("T")


def _require_protobuf() -> None:
    if not _PROTOBUF_AVAILABLE:
        raise ImportError(
            "Protobuf support requires the protobuf package. "
            "Install with: pip install typedkafka[protobuf]"
        )


class ProtobufSerializer(Serializer[Any]):
    """Serializer for Protocol Buffer messages.

    Examples:
        >>> from myapp.proto import UserEvent_pb2
        >>> serializer = ProtobufSerializer()
        >>> event = UserEvent_pb2.UserEvent(user_id=123, action="click")
        >>> data = serializer.serialize("topic", event)
    """

    def __init__(self) -> None:
        _require_protobuf()

    def serialize(self, topic: str, value: Any) -> bytes:
        """Serialize a protobuf message to bytes."""
        try:
            return value.SerializeToString()
        except Exception as e:
            raise SerializationError(
                f"Protobuf serialization failed: {e}",
                value=value,
                original_error=e,
            ) from e


class ProtobufDeserializer(Deserializer[Any]):
    """Deserializer for Protocol Buffer messages.

    Args:
        message_type: The protobuf message class to deserialize into.

    Examples:
        >>> from myapp.proto import UserEvent_pb2
        >>> deserializer = ProtobufDeserializer(UserEvent_pb2.UserEvent)
        >>> event = deserializer.deserialize("topic", raw_bytes)
    """

    def __init__(self, message_type: type[Any]) -> None:
        _require_protobuf()
        self._message_type = message_type

    def deserialize(self, topic: str, data: bytes) -> Any:
        """Deserialize bytes to a protobuf message."""
        try:
            message = self._message_type()
            message.ParseFromString(data)
            return message
        except Exception as e:
            raise SerializationError(
                f"Protobuf deserialization failed: {e}",
                value=data,
                original_error=e,
            ) from e


def protobuf_serializer_for(message_type: type[T]) -> Callable[[T], bytes]:
    """Get a simple serializer function for a specific protobuf message type.

    Useful with ``KafkaConsumer(value_deserializer=...)`` patterns.

    Args:
        message_type: The protobuf message class.

    Returns:
        A function that serializes instances to bytes.
    """
    _require_protobuf()

    def _serialize(value: T) -> bytes:
        return value.SerializeToString()  # type: ignore[union-attr,attr-defined]

    return _serialize


def protobuf_deserializer_for(message_type: type[T]) -> Callable[[bytes], T]:
    """Get a simple deserializer function for a specific protobuf message type.

    Useful with ``KafkaConsumer(value_deserializer=...)`` patterns.

    Args:
        message_type: The protobuf message class.

    Returns:
        A function that deserializes bytes to the message type.
    """
    _require_protobuf()

    def _deserialize(data: bytes) -> T:
        msg = message_type()  # type: ignore[call-arg]
        msg.ParseFromString(data)  # type: ignore[union-attr,attr-defined]
        return msg

    return _deserialize


class SchemaRegistryProtobufSerializer:
    """Protobuf serializer with Confluent Schema Registry integration.

    Args:
        schema_registry_url: URL of the Confluent Schema Registry.
        schema_registry_config: Optional additional config for the schema registry client.

    Examples:
        >>> serializer = SchemaRegistryProtobufSerializer(
        ...     schema_registry_url="http://localhost:8081",
        ... )
    """

    def __init__(
        self,
        schema_registry_url: str,
        schema_registry_config: dict[str, Any] | None = None,
    ):
        _require_protobuf()
        try:
            from confluent_kafka.schema_registry import SchemaRegistryClient
        except ImportError as exc:
            raise ImportError(
                "Schema Registry protobuf support requires confluent-kafka[protobuf]. "
                "Install with: pip install typedkafka[protobuf]"
            ) from exc

        sr_config: dict[str, Any] = {"url": schema_registry_url}
        if schema_registry_config:
            sr_config.update(schema_registry_config)
        self._schema_registry = SchemaRegistryClient(sr_config)
        self._serializers: dict[type, Any] = {}

    def _get_serializer(self, message_type: type[Any]) -> Any:
        from confluent_kafka.schema_registry.protobuf import (
            ProtobufSerializer as ConfluentProtobufSerializer,
        )

        if message_type not in self._serializers:
            self._serializers[message_type] = ConfluentProtobufSerializer(
                self._schema_registry,
                message_type,
            )
        return self._serializers[message_type]

    def serialize(
        self,
        topic: str,
        message: Any,
        message_type: type[Any] | None = None,
    ) -> bytes:
        """Serialize a protobuf message with schema registry.

        Args:
            topic: Target topic name.
            message: The protobuf message instance.
            message_type: Optional message class (defaults to type(message)).

        Returns:
            Serialized bytes with schema registry framing.
        """
        from confluent_kafka.serialization import MessageField, SerializationContext

        msg_type = message_type or type(message)
        serializer = self._get_serializer(msg_type)
        ctx = SerializationContext(topic, MessageField.VALUE)
        try:
            return serializer(message, ctx)
        except Exception as e:
            raise SerializationError(
                f"Schema Registry protobuf serialization failed: {e}",
                value=message,
                original_error=e,
            ) from e
