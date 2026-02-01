"""Tests for Dead Letter Queue module."""

import pytest

from typedkafka.dlq import DeadLetterQueue, process_with_dlq
from typedkafka.testing import MockDeadLetterQueue, MockMessage, MockProducer


class TestDeadLetterQueue:
    """Test DeadLetterQueue with MockProducer."""

    def test_send_routes_to_default_dlq_topic(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer)
        msg = MockMessage("orders", b"data", key=b"k1", partition=2, offset=10)

        dlq.send(msg)

        assert len(producer.messages["orders.dlq"]) == 1
        dlq_msg = producer.messages["orders.dlq"][0]
        assert dlq_msg.value == b"data"
        assert dlq_msg.key == b"k1"

    def test_send_adds_metadata_headers(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer)
        msg = MockMessage("orders", b"data", partition=1, offset=42)

        dlq.send(msg)

        dlq_msg = producer.messages["orders.dlq"][0]
        headers = dict(dlq_msg.headers)
        assert headers["dlq.original.topic"] == b"orders"
        assert headers["dlq.original.partition"] == b"1"
        assert headers["dlq.original.offset"] == b"42"

    def test_send_with_error_adds_error_headers(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer)
        msg = MockMessage("orders", b"data", partition=0, offset=0)
        error = ValueError("bad value")

        dlq.send(msg, error=error)

        dlq_msg = producer.messages["orders.dlq"][0]
        headers = dict(dlq_msg.headers)
        assert headers["dlq.error.message"] == b"bad value"
        assert headers["dlq.error.type"] == b"ValueError"
        assert "dlq.error.traceback" in headers

    def test_send_with_extra_headers(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer)
        msg = MockMessage("t", b"v", partition=0, offset=0)

        dlq.send(msg, extra_headers=[("custom", b"val")])

        dlq_msg = producer.messages["t.dlq"][0]
        assert ("custom", b"val") in dlq_msg.headers

    def test_custom_topic_fn(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer, topic_fn=lambda t: f"errors.{t}")
        msg = MockMessage("orders", b"data", partition=0, offset=0)

        dlq.send(msg)

        assert len(producer.messages["errors.orders"]) == 1

    def test_default_topic(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer, default_topic="all-errors")
        msg = MockMessage("orders", b"data", partition=0, offset=0)

        dlq.send(msg)

        assert len(producer.messages["all-errors"]) == 1

    def test_both_topic_fn_and_default_raises(self):
        producer = MockProducer()
        with pytest.raises(ValueError, match="Cannot specify both"):
            DeadLetterQueue(producer, topic_fn=lambda t: t, default_topic="x")

    def test_send_count_increments(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer)
        msg = MockMessage("t", b"v", partition=0, offset=0)

        assert dlq.send_count == 0
        dlq.send(msg)
        assert dlq.send_count == 1
        dlq.send(msg)
        assert dlq.send_count == 2


class TestProcessWithDlq:
    """Test the process_with_dlq helper."""

    def test_success_returns_true(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer)
        msg = MockMessage("t", b"v", partition=0, offset=0)

        result = process_with_dlq(msg, lambda m: None, dlq)

        assert result is True
        assert dlq.send_count == 0

    def test_failure_returns_false_and_sends_to_dlq(self):
        producer = MockProducer()
        dlq = DeadLetterQueue(producer)
        msg = MockMessage("t", b"v", partition=0, offset=0)

        def bad_handler(m):
            raise RuntimeError("fail")

        result = process_with_dlq(msg, bad_handler, dlq)

        assert result is False
        assert dlq.send_count == 1


class TestMockDeadLetterQueue:
    """Test MockDeadLetterQueue for testing utilities."""

    def test_send_records_message(self):
        dlq = MockDeadLetterQueue()
        msg = MockMessage("orders", b"data", key=b"k", partition=1, offset=5)

        dlq.send(msg)

        assert dlq.send_count == 1
        topic, dlq_msg = dlq.messages[0]
        assert topic == "orders.dlq"
        assert dlq_msg.value == b"data"
        assert dlq_msg.key == b"k"

    def test_send_with_error(self):
        dlq = MockDeadLetterQueue()
        msg = MockMessage("t", b"v", partition=0, offset=0)

        dlq.send(msg, error=ValueError("oops"))

        headers = dict(dlq.messages[0][1].headers)
        assert headers["dlq.error.type"] == b"ValueError"

    def test_custom_topic_fn(self):
        dlq = MockDeadLetterQueue(topic_fn=lambda t: f"dead.{t}")
        msg = MockMessage("orders", b"v", partition=0, offset=0)

        dlq.send(msg)

        assert dlq.messages[0][0] == "dead.orders"

    def test_default_topic(self):
        dlq = MockDeadLetterQueue(default_topic="errors")
        msg = MockMessage("orders", b"v", partition=0, offset=0)

        dlq.send(msg)

        assert dlq.messages[0][0] == "errors"

    def test_both_raises(self):
        with pytest.raises(ValueError):
            MockDeadLetterQueue(topic_fn=lambda t: t, default_topic="x")

    def test_reset_clears(self):
        dlq = MockDeadLetterQueue()
        msg = MockMessage("t", b"v", partition=0, offset=0)
        dlq.send(msg)
        dlq.reset()
        assert dlq.send_count == 0
        assert len(dlq.messages) == 0

    def test_works_with_process_with_dlq(self):
        """MockDeadLetterQueue is compatible with process_with_dlq."""
        dlq = MockDeadLetterQueue()
        msg = MockMessage("t", b"v", partition=0, offset=0)

        def fail(m):
            raise RuntimeError("boom")

        result = process_with_dlq(msg, fail, dlq)

        assert result is False
        assert dlq.send_count == 1
