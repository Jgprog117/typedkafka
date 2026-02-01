"""Extended tests for serializers.py to cover Avro classes and edge cases."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from typedkafka.exceptions import SerializationError
from typedkafka.serializers import (
    AvroDeserializer,
    AvroSerializer,
    StringDeserializer,
    StringSerializer,
)


def _make_mock_serialization_module():
    """Create a mock confluent_kafka.serialization module."""
    mod = ModuleType("confluent_kafka.serialization")
    mod.SerializationContext = MagicMock()  # type: ignore[attr-defined]
    mod.MessageField = MagicMock()  # type: ignore[attr-defined]
    return mod


class TestAvroSerializerWithMock:
    """Test AvroSerializer serialize method with mocked internals."""

    def test_serialize_success(self):
        ser = AvroSerializer.__new__(AvroSerializer)
        ser._registry = MagicMock()
        ser._serializer = MagicMock(return_value=b"avro-data")

        mock_mod = _make_mock_serialization_module()
        with patch.dict(sys.modules, {"confluent_kafka.serialization": mock_mod}):
            result = ser.serialize("topic", {"id": 1})
            assert result == b"avro-data"
            ser._serializer.assert_called_once()

    def test_serialize_error(self):
        ser = AvroSerializer.__new__(AvroSerializer)
        ser._registry = MagicMock()
        ser._serializer = MagicMock(side_effect=RuntimeError("schema fail"))

        mock_mod = _make_mock_serialization_module()
        with patch.dict(sys.modules, {"confluent_kafka.serialization": mock_mod}):
            with pytest.raises(SerializationError, match="Avro serialization failed"):
                ser.serialize("topic", {"id": 1})


class TestAvroDeserializerWithMock:
    """Test AvroDeserializer deserialize method with mocked internals."""

    def test_deserialize_success(self):
        deser = AvroDeserializer.__new__(AvroDeserializer)
        deser._registry = MagicMock()
        deser._deserializer = MagicMock(return_value={"id": 1})

        mock_mod = _make_mock_serialization_module()
        with patch.dict(sys.modules, {"confluent_kafka.serialization": mock_mod}):
            result = deser.deserialize("topic", b"data")
            assert result == {"id": 1}
            deser._deserializer.assert_called_once()

    def test_deserialize_error(self):
        deser = AvroDeserializer.__new__(AvroDeserializer)
        deser._registry = MagicMock()
        deser._deserializer = MagicMock(side_effect=RuntimeError("fail"))

        mock_mod = _make_mock_serialization_module()
        with patch.dict(sys.modules, {"confluent_kafka.serialization": mock_mod}):
            with pytest.raises(SerializationError, match="Avro deserialization failed"):
                deser.deserialize("topic", b"data")


class TestAvroInitWithMock:
    """Test Avro init with mocked schema registry deps."""

    def test_avro_serializer_init_success(self):
        mock_sr_mod = ModuleType("confluent_kafka.schema_registry")
        mock_sr_mod.SchemaRegistryClient = MagicMock()  # type: ignore[attr-defined]
        mock_avro_mod = ModuleType("confluent_kafka.schema_registry.avro")
        mock_avro_mod.AvroSerializer = MagicMock()  # type: ignore[attr-defined]

        with patch.dict(
            sys.modules,
            {
                "confluent_kafka.schema_registry": mock_sr_mod,
                "confluent_kafka.schema_registry.avro": mock_avro_mod,
            },
        ):
            ser = AvroSerializer("http://localhost:8081", '{"type": "string"}')
            assert ser._registry is not None

    def test_avro_serializer_with_extra_config(self):
        mock_sr_mod = ModuleType("confluent_kafka.schema_registry")
        mock_sr_client = MagicMock()
        mock_sr_mod.SchemaRegistryClient = mock_sr_client  # type: ignore[attr-defined]
        mock_avro_mod = ModuleType("confluent_kafka.schema_registry.avro")
        mock_avro_mod.AvroSerializer = MagicMock()  # type: ignore[attr-defined]

        with patch.dict(
            sys.modules,
            {
                "confluent_kafka.schema_registry": mock_sr_mod,
                "confluent_kafka.schema_registry.avro": mock_avro_mod,
            },
        ):
            _ = AvroSerializer(
                "http://localhost:8081",
                '{"type": "string"}',
                schema_registry_config={"basic.auth.user.info": "user:pass"},
            )
            # Check SchemaRegistryClient was called with merged config
            call_config = mock_sr_client.call_args[0][0]
            assert call_config["url"] == "http://localhost:8081"
            assert call_config["basic.auth.user.info"] == "user:pass"

    def test_avro_deserializer_init_success(self):
        mock_sr_mod = ModuleType("confluent_kafka.schema_registry")
        mock_sr_mod.SchemaRegistryClient = MagicMock()  # type: ignore[attr-defined]
        mock_avro_mod = ModuleType("confluent_kafka.schema_registry.avro")
        mock_avro_mod.AvroDeserializer = MagicMock()  # type: ignore[attr-defined]

        with patch.dict(
            sys.modules,
            {
                "confluent_kafka.schema_registry": mock_sr_mod,
                "confluent_kafka.schema_registry.avro": mock_avro_mod,
            },
        ):
            deser = AvroDeserializer("http://localhost:8081")
            assert deser._registry is not None

    def test_avro_deserializer_with_extra_config(self):
        mock_sr_mod = ModuleType("confluent_kafka.schema_registry")
        mock_sr_client = MagicMock()
        mock_sr_mod.SchemaRegistryClient = mock_sr_client  # type: ignore[attr-defined]
        mock_avro_mod = ModuleType("confluent_kafka.schema_registry.avro")
        mock_avro_mod.AvroDeserializer = MagicMock()  # type: ignore[attr-defined]

        with patch.dict(
            sys.modules,
            {
                "confluent_kafka.schema_registry": mock_sr_mod,
                "confluent_kafka.schema_registry.avro": mock_avro_mod,
            },
        ):
            _ = AvroDeserializer(
                "http://localhost:8081",
                schema_registry_config={"basic.auth.user.info": "u:p"},
            )
            call_config = mock_sr_client.call_args[0][0]
            assert call_config["basic.auth.user.info"] == "u:p"


class TestStringSerializerEdgeCases:
    """Additional edge cases for string serializers."""

    def test_custom_encoding_roundtrip(self):
        ser = StringSerializer(encoding="latin-1")
        deser = StringDeserializer(encoding="latin-1")
        text = "café"
        assert deser.deserialize("t", ser.serialize("t", text)) == text

    def test_deserialize_non_bytes_raises(self):
        deser = StringDeserializer()
        with pytest.raises(SerializationError, match="Failed to decode"):
            deser.deserialize("topic", 123)  # type: ignore[arg-type]
