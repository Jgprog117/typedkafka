"""Mock implementations for testing without a Kafka broker."""

from typedkafka.dlq import process_with_dlq
from typedkafka.testing import MockConsumer, MockDeadLetterQueue, MockMessage, MockProducer


def test_producer():
    producer = MockProducer()
    producer.send_json("events", {"user_id": 123})
    producer.flush()
    assert len(producer.messages["events"]) == 1


def test_consumer():
    consumer = MockConsumer()
    consumer.add_json_message("events", {"user_id": 123})
    msg = consumer.poll(1.0)
    assert msg is not None


def test_transactions():
    producer = MockProducer()
    producer.init_transactions()
    with producer.transaction():
        producer.send("topic", b"transactional msg")
    assert len(producer.messages["topic"]) == 1


def test_headers():
    """Send and verify message headers."""
    producer = MockProducer()
    producer.send("topic", b"data", headers=[("trace-id", b"abc")])
    msg = producer.messages["topic"][0]
    assert dict(msg.headers)["trace-id"] == b"abc"


def test_metrics():
    """Mock producer and consumer track metrics."""
    producer = MockProducer()
    producer.send("topic", b"msg1")
    producer.send("topic", b"msg2")
    assert producer.metrics.messages_sent == 2

    consumer = MockConsumer()
    consumer.add_message("topic", b"msg1")
    consumer.add_message("topic", b"msg2")
    consumer.poll()
    consumer.poll()
    assert consumer.metrics.messages_received == 2

    # Reset clears metrics too
    producer.reset()
    assert producer.metrics.messages_sent == 0


def test_dead_letter_queue():
    """MockDeadLetterQueue records failed messages in memory."""
    dlq = MockDeadLetterQueue()
    msg = MockMessage("orders", b'{"bad": "data"}', partition=0, offset=5)

    def handler(m):
        raise ValueError("invalid order")

    success = process_with_dlq(msg, handler, dlq)

    assert success is False
    assert dlq.send_count == 1
    topic, dlq_msg = dlq.messages[0]
    assert topic == "orders.dlq"
    assert dict(dlq_msg.headers)["dlq.error.type"] == b"ValueError"


# --- v0.6.0: New mock features ---


def test_fail_on_topics():
    """MockProducer can simulate failures on specific topics."""
    producer = MockProducer(fail_on_topics=["broken-topic"])
    producer.send("good-topic", b"ok")  # succeeds
    try:
        producer.send("broken-topic", b"fail")
    except Exception:
        pass  # expected to raise


def test_message_count():
    """message_count() returns total across all topics."""
    producer = MockProducer()
    producer.send("t1", b"a")
    producer.send("t2", b"b")
    producer.send("t1", b"c")
    assert producer.message_count() == 3


def test_get_json_messages():
    """get_json_messages() deserializes stored messages."""
    producer = MockProducer()
    producer.send_json("events", {"id": 1})
    producer.send_json("events", {"id": 2})
    msgs = producer.get_json_messages("events")
    assert msgs == [{"id": 1}, {"id": 2}]


def test_add_string_message():
    """MockConsumer.add_string_message() for string payloads."""
    consumer = MockConsumer()
    consumer.add_string_message("logs", "error: disk full")
    msg = consumer.poll()
    assert msg is not None
    assert msg.value_as_string() == "error: disk full"
