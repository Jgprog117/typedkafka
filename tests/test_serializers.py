"""Tests for serializers."""

import pytest

from typedkafka.exceptions import SerializationError
from typedkafka.serializers import (
    JsonDeserializer,
    JsonSerializer,
    StringDeserializer,
    StringSerializer,
)


class TestJsonSerializer:
    """Test JsonSerializer."""

    def test_serialize_dict(self):
        """Test serializing a dict."""
        ser = JsonSerializer()
        result = ser.serialize("topic", {"key": "value"})
        assert result == b'{"key": "value"}'

    def test_serialize_list(self):
        """Test serializing a list."""
        ser = JsonSerializer()
        result = ser.serialize("topic", [1, 2, 3])
        assert result == b"[1, 2, 3]"

    def test_serialize_string(self):
        """Test serializing a string."""
        ser = JsonSerializer()
        result = ser.serialize("topic", "hello")
        assert result == b'"hello"'

    def test_serialize_number(self):
        """Test serializing numbers."""
        ser = JsonSerializer()
        assert ser.serialize("topic", 42) == b"42"
        assert ser.serialize("topic", 3.14) == b"3.14"

    def test_serialize_null(self):
        """Test serializing None."""
        ser = JsonSerializer()
        assert ser.serialize("topic", None) == b"null"

    def test_serialize_non_serializable_raises(self):
        """Test that non-serializable objects raise SerializationError."""
        ser = JsonSerializer()
        with pytest.raises(SerializationError, match="Failed to serialize"):
            ser.serialize("topic", object())

    def test_serialize_nested(self):
        """Test serializing nested structures."""
        ser = JsonSerializer()
        data = {"users": [{"id": 1, "name": "Alice"}]}
        result = ser.serialize("topic", data)
        import json
        assert json.loads(result) == data


class TestJsonDeserializer:
    """Test JsonDeserializer."""

    def test_deserialize_dict(self):
        """Test deserializing a dict."""
        deser = JsonDeserializer()
        result = deser.deserialize("topic", b'{"key": "value"}')
        assert result == {"key": "value"}

    def test_deserialize_list(self):
        """Test deserializing a list."""
        deser = JsonDeserializer()
        result = deser.deserialize("topic", b"[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_deserialize_invalid_json_raises(self):
        """Test that invalid JSON raises SerializationError."""
        deser = JsonDeserializer()
        with pytest.raises(SerializationError, match="Failed to deserialize"):
            deser.deserialize("topic", b"not json")

    def test_deserialize_invalid_encoding_raises(self):
        """Test that invalid encoding raises SerializationError."""
        deser = JsonDeserializer()
        with pytest.raises(SerializationError):
            deser.deserialize("topic", b"\xff\xfe")


class TestStringSerializer:
    """Test StringSerializer."""

    def test_serialize_string(self):
        """Test serializing a string."""
        ser = StringSerializer()
        assert ser.serialize("topic", "hello") == b"hello"

    def test_serialize_unicode(self):
        """Test serializing unicode."""
        ser = StringSerializer()
        assert ser.serialize("topic", "héllo") == "héllo".encode()

    def test_serialize_custom_encoding(self):
        """Test serializing with custom encoding."""
        ser = StringSerializer(encoding="ascii")
        assert ser.serialize("topic", "hello") == b"hello"

    def test_serialize_non_string_raises(self):
        """Test that non-string raises SerializationError."""
        ser = StringSerializer()
        with pytest.raises(SerializationError, match="Failed to encode"):
            ser.serialize("topic", 123)  # type: ignore[arg-type]


class TestStringDeserializer:
    """Test StringDeserializer."""

    def test_deserialize_bytes(self):
        """Test deserializing bytes."""
        deser = StringDeserializer()
        assert deser.deserialize("topic", b"hello") == "hello"

    def test_deserialize_unicode(self):
        """Test deserializing unicode bytes."""
        deser = StringDeserializer()
        assert deser.deserialize("topic", "héllo".encode()) == "héllo"

    def test_deserialize_custom_encoding(self):
        """Test deserializing with custom encoding."""
        deser = StringDeserializer(encoding="ascii")
        assert deser.deserialize("topic", b"hello") == "hello"

    def test_deserialize_invalid_encoding_raises(self):
        """Test that invalid encoding raises SerializationError."""
        deser = StringDeserializer(encoding="ascii")
        with pytest.raises(SerializationError, match="Failed to decode"):
            deser.deserialize("topic", b"\xff\xfe")
