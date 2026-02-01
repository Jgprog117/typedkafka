"""Integration tests for config builders with a real broker."""

from __future__ import annotations

from tests.integration.conftest import KAFKA_BOOTSTRAP, integration


@integration
class TestConfigBuildersIntegration:
    """Test that config builders produce configs that work with real brokers."""

    def test_producer_config_builder(self, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer, ProducerConfig

        config = (
            ProducerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .acks("all")
            .compression("gzip")
            .linger_ms(0)
            .build(validate=True)
        )

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(config) as producer:
                producer.send_json(unique_topic, {"builder": True})
                producer.flush()

            consumer_cfg = {
                "bootstrap.servers": KAFKA_BOOTSTRAP,
                "group.id": "cfg-test-group",
                "auto.offset.reset": "earliest",
            }
            with KafkaConsumer(consumer_cfg) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=10.0)
                assert msg is not None
                assert msg.value_as_json() == {"builder": True}
        finally:
            admin.delete_topic(unique_topic)

    def test_consumer_config_builder(self, unique_topic):
        from typedkafka import ConsumerConfig, KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer({"bootstrap.servers": KAFKA_BOOTSTRAP}) as producer:
                producer.send_string(unique_topic, "from-builder")
                producer.flush()

            config = (
                ConsumerConfig()
                .bootstrap_servers(KAFKA_BOOTSTRAP)
                .group_id("builder-consumer-test")
                .auto_offset_reset("earliest")
                .build(validate=True)
            )

            with KafkaConsumer(config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=10.0)
                assert msg is not None
                assert msg.value_as_string() == "from-builder"
        finally:
            admin.delete_topic(unique_topic)
