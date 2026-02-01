"""Integration tests for advanced producer features."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestAdvancedProducerIntegration:
    """Test advanced producer features against a real broker."""

    def test_send_with_partition(self, producer_config, consumer_config, unique_topic):
        """Test sending to a specific partition."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=3, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"to-partition-1", partition=1)
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.partition == 1
                assert msg.value == b"to-partition-1"
        finally:
            admin.delete_topic(unique_topic)

    def test_flush_returns_zero(self, producer_config, unique_topic):
        """Test flush returns 0 when all messages delivered."""
        from typedkafka import KafkaAdmin, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"msg1")
                producer.send(unique_topic, b"msg2")
                remaining = producer.flush()
                assert remaining == 0
        finally:
            admin.delete_topic(unique_topic)

    def test_context_manager_flushes(self, producer_config, consumer_config, unique_topic):
        """Test that context manager flushes on exit."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"auto-flushed")
                # No explicit flush - context manager should handle it

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.value == b"auto-flushed"
        finally:
            admin.delete_topic(unique_topic)

    def test_send_batch_large(self, producer_config, consumer_config, unique_topic):
        """Test send_batch with many messages."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            messages = [(f"msg-{i}".encode(), f"key-{i}".encode()) for i in range(50)]
            with KafkaProducer(producer_config) as producer:
                producer.send_batch(unique_topic, messages)
                producer.flush()
                assert producer.metrics.messages_sent == 0  # send_batch doesn't track via metrics

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                received = []
                for _ in range(30):
                    batch = consumer.poll_batch(max_messages=100, timeout=2.0)
                    received.extend(batch)
                    if len(received) >= 50:
                        break
                assert len(received) == 50
        finally:
            admin.delete_topic(unique_topic)

    def test_send_string_with_key(self, producer_config, consumer_config, unique_topic):
        """Test send_string with a string key."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_string(unique_topic, "hello", key="my-key")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.value_as_string() == "hello"
                assert msg.key_as_string() == "my-key"
        finally:
            admin.delete_topic(unique_topic)

    def test_send_json_with_none_key(self, producer_config, consumer_config, unique_topic):
        """Test send_json with key=None."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_json(unique_topic, {"id": 1}, key=None)
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.key is None
                assert msg.key_as_string() is None
        finally:
            admin.delete_topic(unique_topic)

    def test_flush_with_timeout(self, producer_config, unique_topic):
        """Test flush with explicit timeout."""
        from typedkafka import KafkaAdmin, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"timed flush")
                remaining = producer.flush(timeout=10.0)
                assert remaining == 0
        finally:
            admin.delete_topic(unique_topic)
