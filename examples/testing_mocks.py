"""Mock implementations for testing without a Kafka broker."""

from typedkafka.testing import MockConsumer, MockProducer


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
