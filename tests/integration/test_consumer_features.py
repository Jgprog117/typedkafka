"""Integration tests for advanced consumer features."""

from __future__ import annotations

from confluent_kafka import TopicPartition

from tests.integration.conftest import integration


@integration
class TestConsumerFeaturesIntegration:
    """Test consumer features against a real broker."""

    def _produce_messages(self, producer_config, topic, count=5):
        from typedkafka import KafkaProducer

        with KafkaProducer(producer_config) as producer:
            for i in range(count):
                producer.send_json(topic, {"index": i})
            producer.flush()

    def test_poll_batch(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            self._produce_messages(producer_config, unique_topic, count=5)

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                # May take a couple of polls for assignment
                msgs: list = []
                for _ in range(10):
                    batch = consumer.poll_batch(max_messages=10, timeout=2.0)
                    msgs.extend(batch)
                    if len(msgs) >= 5:
                        break
                assert len(msgs) == 5
        finally:
            admin.delete_topic(unique_topic)

    def test_consumer_iterator(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            self._produce_messages(producer_config, unique_topic, count=3)

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                consumer.poll_timeout = 5.0
                received = []
                for msg in consumer:
                    received.append(msg.value_as_json())
                    if len(received) >= 3:
                        break
                assert len(received) == 3
                indices = sorted(m["index"] for m in received)
                assert indices == [0, 1, 2]
        finally:
            admin.delete_topic(unique_topic)

    def test_seek_and_position(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            self._produce_messages(producer_config, unique_topic, count=5)

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                # Wait for assignment
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break

                # Seek back to offset 2
                tp = TopicPartition(unique_topic, 0, 2)
                consumer.seek(tp)

                msg = consumer.poll(timeout=5.0)
                assert msg is not None
                data = msg.value_as_json()
                assert data["index"] == 2
        finally:
            admin.delete_topic(unique_topic)

    def test_assignment(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=2, replication_factor=1)

        try:
            # Produce so the consumer gets assigned
            self._produce_messages(producer_config, unique_topic, count=1)

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                # Poll until assigned
                for _ in range(10):
                    consumer.poll(timeout=2.0)
                    assignment = consumer.assignment()
                    if assignment:
                        break

                assert len(assignment) == 2
                topics = {tp.topic for tp in assignment}
                assert topics == {unique_topic}
        finally:
            admin.delete_topic(unique_topic)

    def test_commit_sync(self, producer_config, consumer_config, unique_topic):
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
                # Synchronous commit should not raise
                consumer.commit(msg, asynchronous=False)
        finally:
            admin.delete_topic(unique_topic)

    def test_consumer_metrics(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            self._produce_messages(producer_config, unique_topic, count=3)

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                for _ in range(10):
                    consumer.poll(timeout=2.0)
                    if consumer.metrics.messages_received >= 3:
                        break

                assert consumer.metrics.messages_received >= 3
                assert consumer.metrics.errors == 0
        finally:
            admin.delete_topic(unique_topic)

    def test_message_properties(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_json(unique_topic, {"prop": "test"}, key="k1")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.topic == unique_topic
                assert msg.partition == 0
                assert msg.offset >= 0
                assert msg.timestamp is not None
                assert msg.value_as_json() == {"prop": "test"}
                assert msg.key_as_string() == "k1"
        finally:
            admin.delete_topic(unique_topic)
