"""Tests for protobuf serialization module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from typedkafka.exceptions import SerializationError


class TestRequireProtobuf:
    """Test _require_protobuf guard."""

    def test_raises_when_not_available(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        try:
            pb_mod._PROTOBUF_AVAILABLE = False
            with pytest.raises(ImportError, match="protobuf"):
                pb_mod._require_protobuf()
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_passes_when_available(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        try:
            pb_mod._PROTOBUF_AVAILABLE = True
            pb_mod._require_protobuf()  # should not raise
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original


class TestProtobufSerializer:
    """Test ProtobufSerializer with mocked protobuf."""

    def _make_serializer(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import ProtobufSerializer

            ser = ProtobufSerializer.__new__(ProtobufSerializer)
            return ser
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_serialize_success(self):
        ser = self._make_serializer()
        msg = MagicMock()
        msg.SerializeToString.return_value = b"\x08\x01"
        result = ser.serialize("topic", msg)
        assert result == b"\x08\x01"

    def test_serialize_error(self):
        ser = self._make_serializer()
        msg = MagicMock()
        msg.SerializeToString.side_effect = RuntimeError("bad")
        with pytest.raises(SerializationError, match="Protobuf serialization failed"):
            ser.serialize("topic", msg)

    def test_init_requires_protobuf(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        try:
            pb_mod._PROTOBUF_AVAILABLE = False
            from typedkafka.protobuf import ProtobufSerializer

            with pytest.raises(ImportError, match="protobuf"):
                ProtobufSerializer()
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original


class TestProtobufDeserializer:
    """Test ProtobufDeserializer with mocked protobuf."""

    def test_deserialize_success(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import ProtobufDeserializer

            mock_type = MagicMock()
            mock_instance = MagicMock()
            mock_type.return_value = mock_instance

            deser = ProtobufDeserializer.__new__(ProtobufDeserializer)
            deser._message_type = mock_type
            result = deser.deserialize("topic", b"\x08\x01")
            assert result is mock_instance
            mock_instance.ParseFromString.assert_called_once_with(b"\x08\x01")
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_deserialize_error(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import ProtobufDeserializer

            mock_type = MagicMock()
            mock_type.return_value.ParseFromString.side_effect = RuntimeError("bad")

            deser = ProtobufDeserializer.__new__(ProtobufDeserializer)
            deser._message_type = mock_type
            with pytest.raises(SerializationError, match="Protobuf deserialization failed"):
                deser.deserialize("topic", b"bad")
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_init_requires_protobuf(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        try:
            pb_mod._PROTOBUF_AVAILABLE = False
            from typedkafka.protobuf import ProtobufDeserializer

            with pytest.raises(ImportError, match="protobuf"):
                ProtobufDeserializer(MagicMock)
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original


class TestProtobufHelperFunctions:
    """Test protobuf_serializer_for and protobuf_deserializer_for."""

    def test_serializer_for(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import protobuf_serializer_for

            mock_type = MagicMock()
            fn = protobuf_serializer_for(mock_type)
            msg = MagicMock()
            msg.SerializeToString.return_value = b"data"
            assert fn(msg) == b"data"
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_deserializer_for(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import protobuf_deserializer_for

            mock_type = MagicMock()
            mock_instance = MagicMock()
            mock_type.return_value = mock_instance
            fn = protobuf_deserializer_for(mock_type)
            result = fn(b"data")
            assert result is mock_instance
            mock_instance.ParseFromString.assert_called_once_with(b"data")
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_serializer_for_requires_protobuf(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        try:
            pb_mod._PROTOBUF_AVAILABLE = False
            from typedkafka.protobuf import protobuf_serializer_for

            with pytest.raises(ImportError, match="protobuf"):
                protobuf_serializer_for(MagicMock)
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_deserializer_for_requires_protobuf(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        try:
            pb_mod._PROTOBUF_AVAILABLE = False
            from typedkafka.protobuf import protobuf_deserializer_for

            with pytest.raises(ImportError, match="protobuf"):
                protobuf_deserializer_for(MagicMock)
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original


class TestSchemaRegistryProtobufSerializer:
    """Test SchemaRegistryProtobufSerializer."""

    def test_init_requires_protobuf(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        try:
            pb_mod._PROTOBUF_AVAILABLE = False
            from typedkafka.protobuf import SchemaRegistryProtobufSerializer

            with pytest.raises(ImportError, match="protobuf"):
                SchemaRegistryProtobufSerializer("http://localhost:8081")
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_init_requires_confluent_schema_registry(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import SchemaRegistryProtobufSerializer

            with patch.dict("sys.modules", {"confluent_kafka.schema_registry": None}):
                with pytest.raises(ImportError, match="confluent-kafka"):
                    SchemaRegistryProtobufSerializer("http://localhost:8081")
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_serialize_success(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import SchemaRegistryProtobufSerializer

            sr = SchemaRegistryProtobufSerializer.__new__(SchemaRegistryProtobufSerializer)
            sr._schema_registry = MagicMock()
            sr._serializers = {}

            mock_confluent_ser = MagicMock(return_value=b"framed-data")
            with patch(
                "typedkafka.protobuf.SchemaRegistryProtobufSerializer._get_serializer",
                return_value=mock_confluent_ser,
            ):
                msg = MagicMock()
                result = sr.serialize("topic", msg)
                assert result == b"framed-data"
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_serialize_error(self):
        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import SchemaRegistryProtobufSerializer

            sr = SchemaRegistryProtobufSerializer.__new__(SchemaRegistryProtobufSerializer)
            sr._schema_registry = MagicMock()
            sr._serializers = {}

            mock_confluent_ser = MagicMock(side_effect=RuntimeError("schema error"))
            with patch(
                "typedkafka.protobuf.SchemaRegistryProtobufSerializer._get_serializer",
                return_value=mock_confluent_ser,
            ):
                msg = MagicMock()
                with pytest.raises(SerializationError, match="Schema Registry"):
                    sr.serialize("topic", msg)
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_init_with_extra_config(self):
        import sys
        from types import ModuleType

        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            mock_sr_mod = ModuleType("confluent_kafka.schema_registry")
            mock_sr_client = MagicMock()
            mock_sr_mod.SchemaRegistryClient = mock_sr_client

            with patch.dict(
                sys.modules,
                {"confluent_kafka.schema_registry": mock_sr_mod},
            ):
                from typedkafka.protobuf import SchemaRegistryProtobufSerializer

                _ = SchemaRegistryProtobufSerializer(
                    "http://localhost:8081",
                    schema_registry_config={"basic.auth.user.info": "u:p"},
                )
                call_config = mock_sr_client.call_args[0][0]
                assert call_config["url"] == "http://localhost:8081"
                assert call_config["basic.auth.user.info"] == "u:p"
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original

    def test_get_serializer_caches(self):
        import sys
        from types import ModuleType

        import typedkafka.protobuf as pb_mod

        original = pb_mod._PROTOBUF_AVAILABLE
        pb_mod._PROTOBUF_AVAILABLE = True
        try:
            from typedkafka.protobuf import SchemaRegistryProtobufSerializer

            sr = SchemaRegistryProtobufSerializer.__new__(SchemaRegistryProtobufSerializer)
            sr._schema_registry = MagicMock()
            sr._serializers = {}

            mock_proto_ser = MagicMock()
            mock_proto_mod = ModuleType("confluent_kafka.schema_registry.protobuf")
            mock_proto_mod.ProtobufSerializer = mock_proto_ser

            with patch.dict(
                sys.modules,
                {"confluent_kafka.schema_registry.protobuf": mock_proto_mod},
            ):
                msg_type = type("FakeMsg", (), {})
                s1 = sr._get_serializer(msg_type)
                s2 = sr._get_serializer(msg_type)
                assert s1 is s2
                # Constructor should only be called once (cached)
                assert mock_proto_ser.call_count == 1
        finally:
            pb_mod._PROTOBUF_AVAILABLE = original
