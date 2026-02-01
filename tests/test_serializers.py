"""Tests for serializers."""

from unittest.mock import patch

import pytest

from typedkafka.exceptions import SerializationError
from typedkafka.serializers import (
    Deserializer,
    JsonDeserializer,
    JsonSerializer,
    Serializer,
    StringDeserializer,
    StringSerializer,
)


class TestSerializerABC:
    """Test Serializer abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that Serializer cannot be instantiated."""
        with pytest.raises(TypeError):
            Serializer()  # type: ignore[abstract]

    def test_subclass_must_implement_serialize(self):
        """Test that subclass without serialize() cannot be instantiated."""
        class BadSerializer(Serializer):
            pass

        with pytest.raises(TypeError):
            BadSerializer()  # type: ignore[abstract]

    def test_concrete_subclass_works(self):
        """Test that a proper subclass can be instantiated."""
        class MySerializer(Serializer):
            def serialize(self, topic, value):
                return str(value).encode()

        ser = MySerializer()
        assert ser.serialize("topic", 42) == b"42"


class TestDeserializerABC:
    """Test Deserializer abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that Deserializer cannot be instantiated."""
        with pytest.raises(TypeError):
            Deserializer()  # type: ignore[abstract]

    def test_subclass_must_implement_deserialize(self):
        """Test that subclass without deserialize() cannot be instantiated."""
        class BadDeserializer(Deserializer):
            pass

        with pytest.raises(TypeError):
            BadDeserializer()  # type: ignore[abstract]

    def test_concrete_subclass_works(self):
        """Test that a proper subclass can be instantiated."""
        class MyDeserializer(Deserializer):
            def deserialize(self, topic, data):
                return data.decode()

        deser = MyDeserializer()
        assert deser.deserialize("topic", b"hello") == "hello"


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

    def test_serialize_boolean(self):
        """Test serializing booleans."""
        ser = JsonSerializer()
        assert ser.serialize("topic", True) == b"true"
        assert ser.serialize("topic", False) == b"false"

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

    def test_serialize_returns_bytes(self):
        """Test that output is bytes."""
        ser = JsonSerializer()
        result = ser.serialize("topic", {"key": "value"})
        assert isinstance(result, bytes)
        assert result.decode("utf-8") == '{"key": "value"}'


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

    def test_deserialize_string(self):
        """Test deserializing a string."""
        deser = JsonDeserializer()
        assert deser.deserialize("topic", b'"hello"') == "hello"

    def test_deserialize_number(self):
        """Test deserializing a number."""
        deser = JsonDeserializer()
        assert deser.deserialize("topic", b"42") == 42

    def test_deserialize_null(self):
        """Test deserializing null."""
        deser = JsonDeserializer()
        assert deser.deserialize("topic", b"null") is None

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

    def test_roundtrip(self):
        """Test serializer/deserializer roundtrip."""
        ser = JsonSerializer()
        deser = JsonDeserializer()
        data = {"users": [1, 2, 3], "active": True}
        assert deser.deserialize("t", ser.serialize("t", data)) == data


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

    def test_serialize_empty_string(self):
        """Test serializing empty string."""
        ser = StringSerializer()
        assert ser.serialize("topic", "") == b""

    def test_serialize_custom_encoding(self):
        """Test serializing with custom encoding."""
        ser = StringSerializer(encoding="ascii")
        assert ser.serialize("topic", "hello") == b"hello"

    def test_serialize_non_string_raises(self):
        """Test that non-string raises SerializationError."""
        ser = StringSerializer()
        with pytest.raises(SerializationError, match="Failed to encode"):
            ser.serialize("topic", 123)  # type: ignore[arg-type]

    def test_encoding_stored(self):
        """Test that encoding is stored."""
        ser = StringSerializer(encoding="latin-1")
        assert ser.encoding == "latin-1"


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

    def test_deserialize_empty(self):
        """Test deserializing empty bytes."""
        deser = StringDeserializer()
        assert deser.deserialize("topic", b"") == ""

    def test_deserialize_custom_encoding(self):
        """Test deserializing with custom encoding."""
        deser = StringDeserializer(encoding="ascii")
        assert deser.deserialize("topic", b"hello") == "hello"

    def test_deserialize_invalid_encoding_raises(self):
        """Test that invalid encoding raises SerializationError."""
        deser = StringDeserializer(encoding="ascii")
        with pytest.raises(SerializationError, match="Failed to decode"):
            deser.deserialize("topic", b"\xff\xfe")

    def test_encoding_stored(self):
        """Test that encoding is stored."""
        deser = StringDeserializer(encoding="latin-1")
        assert deser.encoding == "latin-1"

    def test_string_roundtrip(self):
        """Test string serializer/deserializer roundtrip."""
        ser = StringSerializer()
        deser = StringDeserializer()
        text = "Hello, 世界! 🌍"
        assert deser.deserialize("t", ser.serialize("t", text)) == text


class TestAvroSerializerImportError:
    """Test Avro serializer import error handling."""

    def test_avro_serializer_import_error(self):
        """Test AvroSerializer raises ImportError when deps missing."""
        from typedkafka.serializers import AvroSerializer

        with patch.dict("sys.modules", {"confluent_kafka.schema_registry": None}):
            with pytest.raises(ImportError, match="confluent-kafka"):
                AvroSerializer("http://localhost:8081", '{"type": "string"}')

    def test_avro_deserializer_import_error(self):
        """Test AvroDeserializer raises ImportError when deps missing."""
        from typedkafka.serializers import AvroDeserializer

        with patch.dict("sys.modules", {"confluent_kafka.schema_registry": None}):
            with pytest.raises(ImportError, match="confluent-kafka"):
                AvroDeserializer("http://localhost:8081")
