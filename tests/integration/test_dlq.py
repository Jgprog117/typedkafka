"""Integration tests for Dead Letter Queue."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestDLQIntegration:
    """Test DLQ routing against a real broker."""

    def test_dlq_routes_failed_message(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.dlq import DeadLetterQueue, process_with_dlq

        dlq_topic = f"{unique_topic}.dlq"

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        admin.create_topic(dlq_topic, num_partitions=1, replication_factor=1)

        try:
            # Produce a message
            with KafkaProducer(producer_config) as producer:
                producer.send_json(unique_topic, {"will": "fail"})
                producer.flush()

            # Consume and route to DLQ on failure
            with KafkaProducer(producer_config) as dlq_producer:
                dlq = DeadLetterQueue(dlq_producer)

                with KafkaConsumer(consumer_config) as consumer:
                    consumer.subscribe([unique_topic])
                    msg = None
                    for _ in range(10):
                        msg = consumer.poll(timeout=2.0)
                        if msg is not None:
                            break
                    assert msg is not None

                    def failing_handler(m):
                        raise ValueError("processing failed")

                    result = process_with_dlq(msg, failing_handler, dlq)
                    assert result is False
                    assert dlq.send_count == 1

                dlq_producer.flush()

            # Verify message landed in DLQ topic
            dlq_consumer_config = {
                **consumer_config,
                "group.id": "dlq-verify-group",
            }
            with KafkaConsumer(dlq_consumer_config) as consumer:
                consumer.subscribe([dlq_topic])
                dlq_msg = None
                for _ in range(10):
                    dlq_msg = consumer.poll(timeout=2.0)
                    if dlq_msg is not None:
                        break
                assert dlq_msg is not None
                # Original value preserved
                assert dlq_msg.value_as_json() == {"will": "fail"}
                # DLQ headers present
                headers = dict(dlq_msg.headers)
                assert b"processing failed" in headers.get("dlq.error.message", b"")
                assert headers.get("dlq.error.type") == b"ValueError"
                assert b"dlq.original.topic" in headers or "dlq.original.topic" in headers
        finally:
            admin.delete_topic(unique_topic)
            admin.delete_topic(dlq_topic)

    def test_dlq_with_default_topic(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.dlq import DeadLetterQueue

        errors_topic = f"{unique_topic}-errors"

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        admin.create_topic(errors_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_string(unique_topic, "bad-data")
                producer.flush()

            with KafkaProducer(producer_config) as dlq_producer:
                dlq = DeadLetterQueue(dlq_producer, default_topic=errors_topic)

                with KafkaConsumer(consumer_config) as consumer:
                    consumer.subscribe([unique_topic])
                    msg = None
                    for _ in range(10):
                        msg = consumer.poll(timeout=2.0)
                        if msg is not None:
                            break
                    assert msg is not None
                    dlq.send(msg, error=RuntimeError("bad"))

                dlq_producer.flush()

            dlq_consumer_config = {
                **consumer_config,
                "group.id": "dlq-default-verify",
            }
            with KafkaConsumer(dlq_consumer_config) as consumer:
                consumer.subscribe([errors_topic])
                dlq_msg = None
                for _ in range(10):
                    dlq_msg = consumer.poll(timeout=2.0)
                    if dlq_msg is not None:
                        break
                assert dlq_msg is not None
                assert dlq_msg.value_as_string() == "bad-data"
        finally:
            admin.delete_topic(unique_topic)
            admin.delete_topic(errors_topic)
