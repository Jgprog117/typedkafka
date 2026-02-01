"""Integration tests for advanced consumer features."""

from __future__ import annotations

from confluent_kafka import TopicPartition

from tests.integration.conftest import integration


@integration
class TestAdvancedConsumerIntegration:
    """Test advanced consumer features against a real broker."""

    def _produce_messages(self, producer_config, topic, count=5):
        from typedkafka import KafkaProducer

        with KafkaProducer(producer_config) as producer:
            for i in range(count):
                producer.send_json(topic, {"index": i})
            producer.flush()

    def test_manual_assign(self, producer_config, consumer_config, unique_topic):
        """Test manual partition assignment without subscribe."""
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=2, replication_factor=1)

        try:
            self._produce_messages(producer_config, unique_topic, count=3)

            # Remove group.id for manual assignment
            config = {k: v for k, v in consumer_config.items() if k != "group.id"}
            config["group.id"] = f"manual-{unique_topic}"
            with KafkaConsumer(config) as consumer:
                consumer.assign([TopicPartition(unique_topic, 0, 0)])
                msgs = []
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        msgs.append(msg)
                    if msgs:
                        break
                # Should get at least some messages from partition 0
                # (all messages may be on partition 0 or 1 depending on key)
                assignment = consumer.assignment()
                assert len(assignment) == 1
                assert assignment[0].partition == 0
        finally:
            admin.delete_topic(unique_topic)

    def test_position_after_consume(self, producer_config, consumer_config, unique_topic):
        """Test position() returns current offset after consuming."""
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            self._produce_messages(producer_config, unique_topic, count=3)

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                # Consume all messages
                consumed = 0
                for _ in range(20):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        consumed += 1
                    if consumed >= 3:
                        break

                assert consumed >= 3
                positions = consumer.position(
                    [TopicPartition(unique_topic, 0)]
                )
                assert len(positions) == 1
                assert positions[0].offset >= 3
        finally:
            admin.delete_topic(unique_topic)

    def test_commit_async(self, producer_config, consumer_config, unique_topic):
        """Test asynchronous commit."""
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            self._produce_messages(producer_config, unique_topic, count=1)

            consumer_config["enable.auto.commit"] = False
            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                # Async commit should not raise
                consumer.commit(msg, asynchronous=True)
                # Commit all should also work
                consumer.commit()
        finally:
            admin.delete_topic(unique_topic)

    def test_poll_returns_none_on_empty(self, consumer_config, unique_topic):
        """Test poll returns None when no messages available."""
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin({"bootstrap.servers": consumer_config["bootstrap.servers"]})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=2.0)
                assert msg is None
        finally:
            admin.delete_topic(unique_topic)

    def test_value_as_string_encoding(self, producer_config, consumer_config, unique_topic):
        """Test value_as_string with default encoding."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, "héllo wörld".encode())
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.value_as_string() == "héllo wörld"
                assert msg.value_as_string(encoding="utf-8") == "héllo wörld"
        finally:
            admin.delete_topic(unique_topic)

    def test_message_repr(self, producer_config, consumer_config, unique_topic):
        """Test KafkaMessage.__repr__."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"test", key=b"k1")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                r = repr(msg)
                assert "KafkaMessage" in r
                assert unique_topic in r
        finally:
            admin.delete_topic(unique_topic)
