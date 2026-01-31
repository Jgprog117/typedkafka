"""Tests for testing utilities (MockProducer and MockConsumer)."""

import json

from typedkafka.testing import MockConsumer, MockMessage, MockProducer


class TestMockProducer:
    """Test MockProducer functionality."""

    def test_send_records_message(self):
        """Test that send() records messages."""
        producer = MockProducer()
        producer.send("topic1", b"value1", key=b"key1")

        assert len(producer.messages["topic1"]) == 1
        msg = producer.messages["topic1"][0]
        assert msg.value == b"value1"
        assert msg.key == b"key1"
        assert msg.topic == "topic1"

    def test_send_json(self):
        """Test send_json() serializes and records."""
        producer = MockProducer()
        producer.send_json("events", {"user_id": 123, "action": "click"})

        assert len(producer.messages["events"]) == 1
        msg = producer.messages["events"][0]
        data = json.loads(msg.value)
        assert data["user_id"] == 123
        assert data["action"] == "click"

    def test_send_string(self):
        """Test send_string() encodes and records."""
        producer = MockProducer()
        producer.send_string("logs", "Test log message")

        assert len(producer.messages["logs"]) == 1
        msg = producer.messages["logs"][0]
        assert msg.value == b"Test log message"

    def test_flush_marks_flushed(self):
        """Test that flush() marks producer as flushed."""
        producer = MockProducer()
        assert producer.flushed is False

        producer.flush()
        assert producer.flushed is True

    def test_reset_clears_state(self):
        """Test that reset() clears all state."""
        producer = MockProducer()
        producer.send("topic", b"msg")
        producer.flush()

        producer.reset()

        assert len(producer.messages) == 0
        assert producer.call_count == 0
        assert producer.flushed is False

    def test_context_manager(self):
        """Test producer works as context manager."""
        with MockProducer() as producer:
            producer.send("topic", b"msg")
            assert not producer._closed

        assert producer._closed


class TestMockConsumer:
    """Test MockConsumer functionality."""

    def test_add_and_poll_message(self):
        """Test adding and polling messages."""
        consumer = MockConsumer()
        consumer.add_message("topic1", b"value1", key=b"key1")

        msg = consumer.poll()
        assert msg is not None
        assert msg.value == b"value1"
        assert msg.key == b"key1"
        assert msg.topic == "topic1"

    def test_poll_returns_none_when_empty(self):
        """Test poll() returns None when no messages."""
        consumer = MockConsumer()
        msg = consumer.poll()
        assert msg is None

    def test_add_json_message(self):
        """Test adding JSON messages."""
        consumer = MockConsumer()
        consumer.add_json_message("events", {"user_id": 456})

        msg = consumer.poll()
        data = json.loads(msg.value)
        assert data["user_id"] == 456

    def test_subscribe_records_topics(self):
        """Test subscribe() records subscribed topics."""
        consumer = MockConsumer()
        consumer.subscribe(["topic1", "topic2"])

        assert "topic1" in consumer.subscribed_topics
        assert "topic2" in consumer.subscribed_topics

    def test_commit_records_offset(self):
        """Test commit() records committed offsets."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"msg", partition=0, offset=42)

        msg = consumer.poll()
        consumer.commit(msg)

        assert consumer.committed_offsets[("topic", 0)] == 42

    def test_iteration(self):
        """Test iterating over consumer."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"msg1")
        consumer.add_message("topic", b"msg2")
        consumer.add_message("topic", b"msg3")

        messages = list(consumer)
        assert len(messages) == 3
        assert messages[0].value == b"msg1"
        assert messages[1].value == b"msg2"
        assert messages[2].value == b"msg3"

    def test_reset_clears_state(self):
        """Test reset() clears all state."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"msg")
        consumer.subscribe(["topic"])

        consumer.reset()

        assert len(consumer.messages) == 0
        assert len(consumer.subscribed_topics) == 0
        assert len(consumer.committed_offsets) == 0


class TestMockMessage:
    """Test MockMessage functionality."""

    def test_message_attributes(self):
        """Test MockMessage has correct attributes."""
        msg = MockMessage(
            topic="test-topic",
            value=b"test-value",
            key=b"test-key",
            partition=2,
            offset=100,
            headers=[("header-key", b"header-value")],
        )

        assert msg.topic == "test-topic"
        assert msg.value == b"test-value"
        assert msg.key == b"test-key"
        assert msg.partition == 2
        assert msg.offset == 100
        assert len(msg.headers) == 1
        assert msg.headers[0] == ("header-key", b"header-value")
