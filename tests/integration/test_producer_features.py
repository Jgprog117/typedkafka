"""Integration tests for advanced producer features."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestProducerFeaturesIntegration:
    """Test producer features against a real broker."""

    def test_send_batch(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_batch(
                    unique_topic,
                    [
                        (b"msg1", b"key1"),
                        (b"msg2", b"key2"),
                        (b"msg3", None),
                    ],
                )
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msgs = consumer.poll_batch(max_messages=10, timeout=10.0)
                assert len(msgs) == 3
                values = sorted(m.value for m in msgs)
                assert values == [b"msg1", b"msg2", b"msg3"]
        finally:
            admin.delete_topic(unique_topic)

    def test_send_with_headers(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(
                    unique_topic,
                    b"with-headers",
                    headers=[("trace-id", b"abc123"), ("source", b"test")],
                )
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=10.0)
                assert msg is not None
                assert msg.value == b"with-headers"
                headers = msg.headers
                assert headers is not None
                header_dict = dict(headers)
                assert header_dict["trace-id"] == b"abc123"
                assert header_dict["source"] == b"test"
        finally:
            admin.delete_topic(unique_topic)

    def test_send_with_key(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"value", key=b"my-key")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=10.0)
                assert msg is not None
                assert msg.key == b"my-key"
                assert msg.key_as_string() == "my-key"
        finally:
            admin.delete_topic(unique_topic)

    def test_producer_metrics(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                assert producer.metrics.messages_sent == 0
                producer.send(unique_topic, b"m1")
                producer.send(unique_topic, b"m2")
                producer.send(unique_topic, b"m3")
                producer.flush()
                assert producer.metrics.messages_sent == 3
                assert producer.metrics.errors == 0
        finally:
            admin.delete_topic(unique_topic)

    def test_delivery_callback(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        delivered = []

        def on_delivery(err, msg):
            delivered.append((err, msg.topic()))

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"cb-test", on_delivery=on_delivery)
                producer.flush()

            assert len(delivered) == 1
            assert delivered[0][0] is None  # no error
            assert delivered[0][1] == unique_topic
        finally:
            admin.delete_topic(unique_topic)
