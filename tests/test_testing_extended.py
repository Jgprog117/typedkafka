"""Extended tests for testing.py to increase coverage."""

from __future__ import annotations

import pytest

from typedkafka.exceptions import ProducerError, SerializationError
from typedkafka.testing import MockConsumer, MockDeadLetterQueue, MockMessage, MockProducer


class TestMockMessageEdgeCases:
    """Test MockMessage edge cases for uncovered lines."""

    def test_value_as_string_decode_error(self):
        msg = MockMessage(topic="t", value=b"\xff\xfe", partition=0, offset=0)
        with pytest.raises(SerializationError, match="Failed to decode"):
            msg.value_as_string()

    def test_key_as_string_decode_error(self):
        msg = MockMessage(topic="t", value=b"v", key=b"\xff\xfe", partition=0, offset=0)
        with pytest.raises(SerializationError, match="Failed to decode"):
            msg.key_as_string()

    def test_value_as_with_failing_deserializer(self):
        msg = MockMessage(topic="t", value=b"data", partition=0, offset=0)
        with pytest.raises(SerializationError, match="Failed to deserialize"):
            msg.value_as(lambda b: 1 / 0)

    def test_value_as_success(self):
        msg = MockMessage(topic="t", value=b'{"a":1}', partition=0, offset=0)
        import json

        result = msg.value_as(lambda b: json.loads(b))
        assert result == {"a": 1}


class TestMockProducerEdgeCases:
    """Test MockProducer edge cases."""

    def test_fail_on_topics_with_delivery_callback(self):
        cb_called = []

        def cb(err, msg):
            cb_called.append((err, msg))

        producer = MockProducer(fail_on_topics={"bad-topic"})
        with pytest.raises(ProducerError, match="Mock failure"):
            producer.send("bad-topic", b"data", on_delivery=cb)
        assert len(cb_called) == 1
        assert cb_called[0][1] is None

    def test_message_count(self):
        producer = MockProducer()
        assert producer.message_count("t") == 0
        producer.send("t", b"v1")
        producer.send("t", b"v2")
        assert producer.message_count("t") == 2

    def test_get_json_messages(self):
        producer = MockProducer()
        import json

        producer.send("t", json.dumps({"a": 1}).encode())
        producer.send("t", json.dumps({"b": 2}).encode())
        result = producer.get_json_messages("t")
        assert result == [{"a": 1}, {"b": 2}]


class TestMockConsumerEdgeCases:
    """Test MockConsumer edge cases."""

    def test_add_string_message(self):
        consumer = MockConsumer()
        consumer.add_string_message("t", "hello", key="k1")
        msg = consumer.poll()
        assert msg is not None
        assert msg.value == b"hello"
        assert msg.key == b"k1"

    def test_add_string_message_no_key(self):
        consumer = MockConsumer()
        consumer.add_string_message("t", "hello")
        msg = consumer.poll()
        assert msg is not None
        assert msg.value == b"hello"
        assert msg.key is None

    def test_metrics_property(self):
        consumer = MockConsumer()
        from typedkafka.metrics import KafkaMetrics

        assert isinstance(consumer.metrics, KafkaMetrics)


class TestMockDeadLetterQueueEdgeCases:
    """Test MockDeadLetterQueue extra_headers."""

    def test_send_with_extra_headers(self):
        dlq = MockDeadLetterQueue()
        msg = MockMessage(topic="src", value=b"v", partition=0, offset=0)
        error = ValueError("bad data")
        dlq.send(msg, error=error, extra_headers=[("custom", b"val")])
        assert len(dlq.messages) == 1
        _, dlq_msg = dlq.messages[0]
        header_keys = [h[0] for h in dlq_msg.headers]
        assert "custom" in header_keys
        assert "dlq.error.message" in header_keys
