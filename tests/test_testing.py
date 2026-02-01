"""Tests for testing utilities (MockProducer and MockConsumer)."""

import json

import pytest

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

    def test_send_increments_call_count(self):
        """Test that call_count increments on each send."""
        producer = MockProducer()
        assert producer.call_count == 0
        producer.send("topic", b"v1")
        assert producer.call_count == 1
        producer.send("topic", b"v2")
        assert producer.call_count == 2

    def test_send_with_partition(self):
        """Test that partition is recorded."""
        producer = MockProducer()
        producer.send("topic", b"val", partition=3)
        assert producer.messages["topic"][0].partition == 3

    def test_send_default_partition(self):
        """Test that default partition is 0."""
        producer = MockProducer()
        producer.send("topic", b"val")
        assert producer.messages["topic"][0].partition == 0

    def test_send_with_delivery_callback(self):
        """Test that on_delivery callback is called."""
        delivered = []
        producer = MockProducer()
        producer.send("topic", b"val", on_delivery=lambda err, msg: delivered.append((err, msg)))
        assert len(delivered) == 1
        assert delivered[0][0] is None  # no error
        assert delivered[0][1].value == b"val"

    def test_send_json(self):
        """Test send_json() serializes and records."""
        producer = MockProducer()
        producer.send_json("events", {"user_id": 123, "action": "click"})

        assert len(producer.messages["events"]) == 1
        msg = producer.messages["events"][0]
        data = json.loads(msg.value)
        assert data["user_id"] == 123
        assert data["action"] == "click"

    def test_send_json_with_key(self):
        """Test send_json with string key."""
        producer = MockProducer()
        producer.send_json("topic", {"a": 1}, key="my-key")
        msg = producer.messages["topic"][0]
        assert msg.key == b"my-key"

    def test_send_string(self):
        """Test send_string() encodes and records."""
        producer = MockProducer()
        producer.send_string("logs", "Test log message")

        assert len(producer.messages["logs"]) == 1
        msg = producer.messages["logs"][0]
        assert msg.value == b"Test log message"

    def test_send_string_with_key(self):
        """Test send_string with string key."""
        producer = MockProducer()
        producer.send_string("topic", "val", key="k")
        assert producer.messages["topic"][0].key == b"k"

    def test_send_batch(self):
        """Test send_batch records all messages."""
        producer = MockProducer()
        producer.send_batch("topic", [
            (b"v1", b"k1"),
            (b"v2", None),
            (b"v3", b"k3"),
        ])
        assert len(producer.messages["topic"]) == 3
        assert producer.messages["topic"][0].value == b"v1"
        assert producer.messages["topic"][0].key == b"k1"
        assert producer.messages["topic"][1].key is None
        assert producer.call_count == 3

    def test_send_batch_with_callback(self):
        """Test send_batch invokes callback for each message."""
        delivered = []
        producer = MockProducer()
        producer.send_batch(
            "topic",
            [(b"v1", None), (b"v2", None)],
            on_delivery=lambda err, msg: delivered.append(msg),
        )
        assert len(delivered) == 2

    def test_flush_marks_flushed(self):
        """Test that flush() marks producer as flushed."""
        producer = MockProducer()
        assert producer.flushed is False

        result = producer.flush()
        assert producer.flushed is True
        assert result == 0

    def test_close_marks_closed_and_flushes(self):
        """Test that close() marks closed and flushes."""
        producer = MockProducer()
        producer.close()
        assert producer._closed is True
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
        assert producer._closed is False

    def test_context_manager(self):
        """Test producer works as context manager."""
        with MockProducer() as producer:
            producer.send("topic", b"msg")
            assert not producer._closed

        assert producer._closed

    def test_multiple_topics(self):
        """Test sending to multiple topics."""
        producer = MockProducer()
        producer.send("t1", b"v1")
        producer.send("t2", b"v2")
        producer.send("t1", b"v3")

        assert len(producer.messages["t1"]) == 2
        assert len(producer.messages["t2"]) == 1

    def test_offsets_auto_increment(self):
        """Test that offsets auto-increment per topic."""
        producer = MockProducer()
        producer.send("topic", b"v1")
        producer.send("topic", b"v2")
        assert producer.messages["topic"][0].offset == 0
        assert producer.messages["topic"][1].offset == 1

    def test_config_stored(self):
        """Test that config is stored."""
        producer = MockProducer({"bootstrap.servers": "localhost:9092"})
        assert producer.config["bootstrap.servers"] == "localhost:9092"

    def test_config_defaults_to_empty(self):
        """Test that config defaults to empty dict."""
        producer = MockProducer()
        assert producer.config == {}


class TestMockProducerTransactions:
    """Test MockProducer transaction support."""

    def test_transaction_commit(self):
        """Test that committed transactions flush messages."""
        producer = MockProducer()
        producer.init_transactions()
        producer.begin_transaction()
        producer.send("topic", b"v1")
        producer.send("topic", b"v2")

        # Messages are buffered during transaction
        assert len(producer.messages["topic"]) == 0

        producer.commit_transaction()
        assert len(producer.messages["topic"]) == 2

    def test_transaction_abort(self):
        """Test that aborted transactions discard messages."""
        producer = MockProducer()
        producer.init_transactions()
        producer.begin_transaction()
        producer.send("topic", b"v1")
        producer.abort_transaction()

        assert len(producer.messages["topic"]) == 0

    def test_transaction_context_manager_commit(self):
        """Test transaction context manager commits on clean exit."""
        producer = MockProducer()
        producer.init_transactions()
        with producer.transaction():
            producer.send("topic", b"v1")

        assert len(producer.messages["topic"]) == 1

    def test_transaction_context_manager_abort(self):
        """Test transaction context manager aborts on exception."""
        producer = MockProducer()
        producer.init_transactions()

        with pytest.raises(ValueError):
            with producer.transaction():
                producer.send("topic", b"v1")
                raise ValueError("oops")

        assert len(producer.messages["topic"]) == 0

    def test_reset_clears_transaction_state(self):
        """Test reset clears transaction state."""
        producer = MockProducer()
        producer.begin_transaction()
        producer.send("topic", b"v1")
        producer.reset()
        assert not producer._in_transaction
        assert len(producer._transaction_messages) == 0


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

    def test_poll_order(self):
        """Test messages are polled in order."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"v1")
        consumer.add_message("topic", b"v2")
        consumer.add_message("topic", b"v3")

        assert consumer.poll().value == b"v1"
        assert consumer.poll().value == b"v2"
        assert consumer.poll().value == b"v3"
        assert consumer.poll() is None

    def test_add_json_message(self):
        """Test adding JSON messages."""
        consumer = MockConsumer()
        consumer.add_json_message("events", {"user_id": 456})

        msg = consumer.poll()
        data = json.loads(msg.value)
        assert data["user_id"] == 456

    def test_add_json_message_with_key(self):
        """Test adding JSON message with string key."""
        consumer = MockConsumer()
        consumer.add_json_message("events", {"a": 1}, key="k1")
        msg = consumer.poll()
        assert msg.key == b"k1"

    def test_subscribe_records_topics(self):
        """Test subscribe() records subscribed topics."""
        consumer = MockConsumer()
        consumer.subscribe(["topic1", "topic2"])

        assert "topic1" in consumer.subscribed_topics
        assert "topic2" in consumer.subscribed_topics

    def test_subscribe_with_callbacks(self):
        """Test subscribe accepts rebalance callback kwargs."""
        consumer = MockConsumer()

        def on_assign(c, p):
            pass

        def on_revoke(c, p):
            pass

        consumer.subscribe(["topic"], on_assign=on_assign, on_revoke=on_revoke)
        assert consumer.subscribed_topics == ["topic"]

    def test_commit_records_offset(self):
        """Test commit() records committed offsets."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"msg", partition=0, offset=42)

        msg = consumer.poll()
        consumer.commit(msg)

        assert consumer.committed_offsets[("topic", 0)] == 42

    def test_commit_without_message(self):
        """Test commit without message is a no-op."""
        consumer = MockConsumer()
        consumer.commit()  # should not raise

    def test_commit_multiple_partitions(self):
        """Test committing across multiple partitions."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"v1", partition=0, offset=10)
        consumer.add_message("topic", b"v2", partition=1, offset=20)

        msg1 = consumer.poll()
        consumer.commit(msg1)
        msg2 = consumer.poll()
        consumer.commit(msg2)

        assert consumer.committed_offsets[("topic", 0)] == 10
        assert consumer.committed_offsets[("topic", 1)] == 20

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

    def test_close_marks_closed(self):
        """Test close() marks consumer as closed."""
        consumer = MockConsumer()
        consumer.close()
        assert consumer._closed is True

    def test_context_manager(self):
        """Test consumer works as context manager."""
        with MockConsumer() as consumer:
            consumer.add_message("topic", b"msg")
            assert not consumer._closed
        assert consumer._closed

    def test_auto_offset_generation(self):
        """Test that offsets are auto-generated."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"v1")
        consumer.add_message("topic", b"v2")
        assert consumer.messages[0].offset == 0
        assert consumer.messages[1].offset == 1

    def test_custom_offset(self):
        """Test that custom offsets are honored."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"v1", offset=100)
        assert consumer.messages[0].offset == 100

    def test_headers(self):
        """Test message headers."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"v1", headers=[("h1", b"hv1")])
        msg = consumer.poll()
        assert msg.headers == [("h1", b"hv1")]

    def test_poll_timeout_attribute(self):
        """Test that poll_timeout attribute exists."""
        consumer = MockConsumer()
        assert consumer.poll_timeout == 1.0
        consumer.poll_timeout = 5.0
        assert consumer.poll_timeout == 5.0

    def test_config_stored(self):
        """Test that config is stored."""
        consumer = MockConsumer({"group.id": "test"})
        assert consumer.config["group.id"] == "test"


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

    def test_message_defaults(self):
        """Test MockMessage default values."""
        msg = MockMessage(topic="t", value=b"v")
        assert msg.key is None
        assert msg.partition == 0
        assert msg.offset == 0
        assert msg.headers == []
        assert msg.timestamp == 0
        assert msg.timestamp_type == 0

    def test_value_as_string(self):
        """Test MockMessage.value_as_string()."""
        msg = MockMessage(topic="t", value=b"hello world")
        assert msg.value_as_string() == "hello world"

    def test_value_as_string_custom_encoding(self):
        """Test MockMessage.value_as_string() with custom encoding."""
        msg = MockMessage(topic="t", value=b"hello")
        assert msg.value_as_string(encoding="ascii") == "hello"

    def test_value_as_json(self):
        """Test MockMessage.value_as_json()."""
        msg = MockMessage(topic="t", value=b'{"user_id": 123}')
        data = msg.value_as_json()
        assert data == {"user_id": 123}

    def test_value_as_json_list(self):
        """Test MockMessage.value_as_json() with list."""
        msg = MockMessage(topic="t", value=b"[1, 2, 3]")
        assert msg.value_as_json() == [1, 2, 3]

    def test_value_as_json_invalid_raises(self):
        """Test MockMessage.value_as_json() raises on invalid JSON."""
        from typedkafka.exceptions import SerializationError

        msg = MockMessage(topic="t", value=b"not json")
        with pytest.raises(SerializationError):
            msg.value_as_json()

    def test_key_as_string(self):
        """Test MockMessage.key_as_string()."""
        msg = MockMessage(topic="t", value=b"v", key=b"my-key")
        assert msg.key_as_string() == "my-key"

    def test_key_as_string_none(self):
        """Test MockMessage.key_as_string() returns None when key is None."""
        msg = MockMessage(topic="t", value=b"v")
        assert msg.key_as_string() is None

    def test_repr(self):
        """Test MockMessage.__repr__()."""
        msg = MockMessage(topic="t", value=b"v", key=b"k", partition=1, offset=42)
        r = repr(msg)
        assert "MockMessage" in r
        assert "t" in r
        assert "42" in r


class TestMockConsumerOffsetManagement:
    """Test MockConsumer offset management methods."""

    def test_assign(self):
        """Test assign() stores partitions."""
        consumer = MockConsumer()
        consumer.assign(["tp1", "tp2"])
        assert consumer.assignment() == ["tp1", "tp2"]

    def test_assignment_returns_copy(self):
        """Test assignment() returns a copy."""
        consumer = MockConsumer()
        consumer.assign(["tp1"])
        result = consumer.assignment()
        result.append("tp2")
        assert consumer.assignment() == ["tp1"]

    def test_seek_does_not_raise(self):
        """Test seek() is a no-op but doesn't raise."""
        consumer = MockConsumer()
        consumer.seek("some_partition")

    def test_position_returns_input(self):
        """Test position() returns a copy of input."""
        consumer = MockConsumer()
        result = consumer.position(["tp1"])
        assert result == ["tp1"]

    def test_poll_batch(self):
        """Test poll_batch() returns multiple messages."""
        consumer = MockConsumer()
        consumer.add_message("topic", b"v1")
        consumer.add_message("topic", b"v2")
        consumer.add_message("topic", b"v3")

        batch = consumer.poll_batch(max_messages=2)
        assert len(batch) == 2
        assert batch[0].value == b"v1"
        assert batch[1].value == b"v2"

        # Remaining message
        batch2 = consumer.poll_batch(max_messages=10)
        assert len(batch2) == 1
        assert batch2[0].value == b"v3"

    def test_poll_batch_empty(self):
        """Test poll_batch() returns empty list when no messages."""
        consumer = MockConsumer()
        assert consumer.poll_batch() == []

    def test_reset_clears_assignment(self):
        """Test reset() clears assignment."""
        consumer = MockConsumer()
        consumer.assign(["tp1"])
        consumer.reset()
        assert consumer.assignment() == []
