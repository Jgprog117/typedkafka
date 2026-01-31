"""
Serialization framework for typedkafka.

Provides a pluggable serializer/deserializer interface and built-in
implementations for JSON, String, and Avro (with optional schema registry).
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

from typedkafka.exceptions import SerializationError

T = TypeVar("T")


class Serializer(ABC, Generic[T]):
    """
    Abstract base class for message serializers.

    Implement this interface to create custom serializers for use
    with KafkaProducer.

    Examples:
        >>> class MySerializer(Serializer[dict]):
        ...     def serialize(self, topic, value):
        ...         return json.dumps(value).encode()
    """

    @abstractmethod
    def serialize(self, topic: str, value: T) -> bytes:
        """
        Serialize a value to bytes.

        Args:
            topic: The topic the message will be sent to.
            value: The value to serialize.

        Returns:
            Serialized bytes.
        """
        ...


class Deserializer(ABC, Generic[T]):
    """
    Abstract base class for message deserializers.

    Implement this interface to create custom deserializers for use
    with KafkaConsumer.

    Examples:
        >>> class MyDeserializer(Deserializer[dict]):
        ...     def deserialize(self, topic, data):
        ...         return json.loads(data.decode())
    """

    @abstractmethod
    def deserialize(self, topic: str, data: bytes) -> T:
        """
        Deserialize bytes to a value.

        Args:
            topic: The topic the message came from.
            data: Raw bytes to deserialize.

        Returns:
            Deserialized value.
        """
        ...


class JsonSerializer(Serializer[Any]):
    """
    JSON serializer that encodes Python objects to UTF-8 JSON bytes.

    Examples:
        >>> ser = JsonSerializer()
        >>> ser.serialize("topic", {"user_id": 123})
        b'{"user_id": 123}'
    """

    def serialize(self, topic: str, value: Any) -> bytes:
        """Serialize a value to JSON bytes."""
        try:
            return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise SerializationError(
                f"Failed to serialize value to JSON: {e}",
                value=value,
                original_error=e,
            ) from e


class JsonDeserializer(Deserializer[Any]):
    """
    JSON deserializer that decodes UTF-8 JSON bytes to Python objects.

    Examples:
        >>> deser = JsonDeserializer()
        >>> deser.deserialize("topic", b'{"user_id": 123}')
        {'user_id': 123}
    """

    def deserialize(self, topic: str, data: bytes) -> Any:
        """Deserialize JSON bytes to a Python object."""
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise SerializationError(
                f"Failed to deserialize JSON: {e}",
                value=data,
                original_error=e,
            ) from e


class StringSerializer(Serializer[str]):
    """
    String serializer that encodes strings to bytes.

    Args:
        encoding: Character encoding to use (default: utf-8).

    Examples:
        >>> ser = StringSerializer()
        >>> ser.serialize("topic", "hello")
        b'hello'
    """

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def serialize(self, topic: str, value: str) -> bytes:
        """Serialize a string to bytes."""
        try:
            return value.encode(self.encoding)
        except (UnicodeEncodeError, AttributeError) as e:
            raise SerializationError(
                f"Failed to encode string: {e}",
                value=value,
                original_error=e,
            ) from e


class StringDeserializer(Deserializer[str]):
    """
    String deserializer that decodes bytes to strings.

    Args:
        encoding: Character encoding to use (default: utf-8).

    Examples:
        >>> deser = StringDeserializer()
        >>> deser.deserialize("topic", b"hello")
        'hello'
    """

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def deserialize(self, topic: str, data: bytes) -> str:
        """Deserialize bytes to a string."""
        try:
            return data.decode(self.encoding)
        except (UnicodeDecodeError, AttributeError) as e:
            raise SerializationError(
                f"Failed to decode bytes as {self.encoding}: {e}",
                value=data,
                original_error=e,
            ) from e


class AvroSerializer(Serializer[Any]):
    """
    Avro serializer with Confluent Schema Registry support.

    Requires the ``confluent-kafka[avro]`` or ``fastavro`` package
    and a running Schema Registry.

    Args:
        schema_registry_url: URL of the Confluent Schema Registry.
        schema_str: Avro schema as a JSON string.
        schema_registry_config: Optional additional config for the schema registry client.

    Raises:
        ImportError: If required schema registry dependencies are not installed.

    Examples:
        >>> schema = '{"type": "record", "name": "User", "fields": [{"name": "id", "type": "int"}]}'
        >>> ser = AvroSerializer("http://localhost:8081", schema)
        >>> ser.serialize("users", {"id": 123})
    """

    def __init__(
        self,
        schema_registry_url: str,
        schema_str: str,
        schema_registry_config: Optional[dict[str, Any]] = None,
    ):
        try:
            from confluent_kafka.schema_registry import SchemaRegistryClient
            from confluent_kafka.schema_registry.avro import AvroSerializer as _AvroSerializer
        except ImportError as exc:
            raise ImportError(
                "Schema Registry support requires confluent-kafka[avro]. "
                "Install with: pip install confluent-kafka[avro]"
            ) from exc

        sr_config: dict[str, Any] = {"url": schema_registry_url}
        if schema_registry_config:
            sr_config.update(schema_registry_config)

        self._registry = SchemaRegistryClient(sr_config)
        self._serializer = _AvroSerializer(
            self._registry,
            schema_str,
        )

    def serialize(self, topic: str, value: Any) -> bytes:
        """Serialize a value using Avro with Schema Registry."""
        try:
            from confluent_kafka.serialization import MessageField, SerializationContext

            ctx = SerializationContext(topic, MessageField.VALUE)
            return self._serializer(value, ctx)
        except Exception as e:
            raise SerializationError(
                f"Avro serialization failed: {e}",
                value=value,
                original_error=e,
            ) from e


class AvroDeserializer(Deserializer[Any]):
    """
    Avro deserializer with Confluent Schema Registry support.

    Requires the ``confluent-kafka[avro]`` package and a running Schema Registry.

    Args:
        schema_registry_url: URL of the Confluent Schema Registry.
        schema_str: Optional Avro schema as a JSON string. If not provided,
            the schema is fetched from the registry.
        schema_registry_config: Optional additional config for the schema registry client.

    Raises:
        ImportError: If required schema registry dependencies are not installed.

    Examples:
        >>> deser = AvroDeserializer("http://localhost:8081")
        >>> data = deser.deserialize("users", raw_bytes)
    """

    def __init__(
        self,
        schema_registry_url: str,
        schema_str: Optional[str] = None,
        schema_registry_config: Optional[dict[str, Any]] = None,
    ):
        try:
            from confluent_kafka.schema_registry import SchemaRegistryClient
            from confluent_kafka.schema_registry.avro import (
                AvroDeserializer as _AvroDeserializer,
            )
        except ImportError as exc:
            raise ImportError(
                "Schema Registry support requires confluent-kafka[avro]. "
                "Install with: pip install confluent-kafka[avro]"
            ) from exc

        sr_config: dict[str, Any] = {"url": schema_registry_url}
        if schema_registry_config:
            sr_config.update(schema_registry_config)

        self._registry = SchemaRegistryClient(sr_config)
        self._deserializer = _AvroDeserializer(
            self._registry,
            schema_str,
        )

    def deserialize(self, topic: str, data: bytes) -> Any:
        """Deserialize Avro bytes using Schema Registry."""
        try:
            from confluent_kafka.serialization import MessageField, SerializationContext

            ctx = SerializationContext(topic, MessageField.VALUE)
            return self._deserializer(data, ctx)
        except Exception as e:
            raise SerializationError(
                f"Avro deserialization failed: {e}",
                value=data,
                original_error=e,
            ) from e
