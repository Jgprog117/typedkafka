"""Tests for TypedTopic, send_typed, and decode."""

from unittest.mock import MagicMock

import pytest

from typedkafka.exceptions import SerializationError
from typedkafka.metrics import KafkaMetrics
from typedkafka.serializers import (
    JsonDeserializer,
    JsonSerializer,
    StringDeserializer,
    StringSerializer,
)
from typedkafka.topics import TypedTopic, json_topic, string_topic


class TestTypedTopic:
    """Test TypedTopic class."""

    def test_init(self):
        topic = TypedTopic("test", JsonSerializer(), JsonDeserializer())
        assert topic.name == "test"
        assert isinstance(topic.value_serializer, JsonSerializer)
        assert isinstance(topic.value_deserializer, JsonDeserializer)
        assert topic.key_serializer is None
        assert topic.key_deserializer is None

    def test_init_with_key_serializers(self):
        topic = TypedTopic(
            "test",
            JsonSerializer(),
            JsonDeserializer(),
            key_serializer=StringSerializer(),
            key_deserializer=StringDeserializer(),
        )
        assert isinstance(topic.key_serializer, StringSerializer)

    def test_repr(self):
        topic = TypedTopic("my-topic", JsonSerializer(), JsonDeserializer())
        assert repr(topic) == "TypedTopic(name='my-topic')"


class TestFactoryFunctions:
    """Test json_topic and string_topic factories."""

    def test_json_topic(self):
        topic = json_topic("events")
        assert topic.name == "events"
        assert isinstance(topic.value_serializer, JsonSerializer)
        assert isinstance(topic.value_deserializer, JsonDeserializer)

    def test_string_topic(self):
        topic = string_topic("logs")
        assert topic.name == "logs"
        assert isinstance(topic.value_serializer, StringSerializer)
        assert isinstance(topic.value_deserializer, StringDeserializer)

    def test_string_topic_custom_encoding(self):
        topic = string_topic("logs", encoding="latin-1")
        assert topic.value_serializer.encoding == "latin-1"


class TestProducerSendTyped:
    """Test KafkaProducer.send_typed()."""

    @pytest.fixture
    def producer(self):
        from typedkafka.producer import KafkaProducer

        p = KafkaProducer.__new__(KafkaProducer)
        p.config = {}
        p._producer = MagicMock()
        p._metrics = KafkaMetrics()
        p._logger = None
        return p

    def test_send_typed_json(self, producer):
        topic = json_topic("events")
        producer.send_typed(topic, {"user_id": 123})

        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["topic"] == "events"
        assert b"user_id" in call_args.kwargs["value"]

    def test_send_typed_string(self, producer):
        topic = string_topic("logs")
        producer.send_typed(topic, "hello world")

        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["value"] == b"hello world"

    def test_send_typed_with_key(self, producer):
        topic = TypedTopic(
            "events",
            JsonSerializer(),
            JsonDeserializer(),
            key_serializer=StringSerializer(),
        )
        producer.send_typed(topic, {"id": 1}, key="user-123")

        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["key"] == b"user-123"

    def test_send_typed_key_without_serializer_raises(self, producer):
        topic = json_topic("events")
        with pytest.raises(SerializationError, match="no key_serializer"):
            producer.send_typed(topic, {"id": 1}, key="some-key")

    def test_send_typed_serialization_error(self, producer):
        topic = json_topic("events")
        with pytest.raises(SerializationError, match="Failed to serialize value"):
            producer.send_typed(topic, object())  # not JSON serializable

    def test_send_typed_with_partition_and_headers(self, producer):
        topic = json_topic("events")
        producer.send_typed(
            topic, {"id": 1}, partition=3, headers=[("trace", b"abc")]
        )
        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["partition"] == 3
        assert call_args.kwargs["headers"] == [("trace", b"abc")]


class TestMessageDecode:
    """Test KafkaMessage.decode()."""

    @pytest.fixture
    def make_message(self):
        from typedkafka.consumer import KafkaMessage

        def _make(value: bytes):
            raw = MagicMock()
            raw.topic.return_value = "events"
            raw.partition.return_value = 0
            raw.offset.return_value = 42
            raw.key.return_value = None
            raw.value.return_value = value
            raw.timestamp.return_value = (0, 0)
            raw.headers.return_value = []
            return KafkaMessage(raw)

        return _make

    def test_decode_json(self, make_message):
        msg = make_message(b'{"user_id": 123}')
        topic = json_topic("events")
        data = msg.decode(topic)
        assert data == {"user_id": 123}

    def test_decode_string(self, make_message):
        msg = make_message(b"hello world")
        topic = string_topic("logs")
        text = msg.decode(topic)
        assert text == "hello world"

    def test_decode_error(self, make_message):
        msg = make_message(b"not json")
        topic = json_topic("events")
        with pytest.raises(SerializationError, match="Failed to deserialize"):
            msg.decode(topic)
