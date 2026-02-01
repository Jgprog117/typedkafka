"""Integration tests for config builders with a real broker."""

from __future__ import annotations

from tests.integration.conftest import KAFKA_BOOTSTRAP, integration


@integration
class TestConfigBuildersExtendedIntegration:
    """Test config builder features against a real broker."""

    def test_producer_high_throughput_preset(self, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.config import ProducerConfig

        config = ProducerConfig.high_throughput(KAFKA_BOOTSTRAP)
        built = config.build()

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(built) as producer:
                producer.send_json(unique_topic, {"preset": "high_throughput"})
                producer.flush()
        finally:
            admin.delete_topic(unique_topic)

    def test_consumer_config_build_and_consume(self, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.config import ConsumerConfig

        config = (
            ConsumerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .group_id(f"test-config-{unique_topic}")
            .auto_offset_reset("earliest")
            .enable_auto_commit(False)
            .build()
        )

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer({"bootstrap.servers": KAFKA_BOOTSTRAP}) as producer:
                producer.send_json(unique_topic, {"config": "test"})
                producer.flush()

            with KafkaConsumer(config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.value_as_json() == {"config": "test"}
        finally:
            admin.delete_topic(unique_topic)

    def test_producer_config_with_compression(self, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.config import ConsumerConfig, ProducerConfig

        prod_config = (
            ProducerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .compression("gzip")
            .build()
        )

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(prod_config) as producer:
                producer.send_json(unique_topic, {"compressed": True})
                producer.flush()

            cons_config = (
                ConsumerConfig()
                .bootstrap_servers(KAFKA_BOOTSTRAP)
                .group_id(f"test-comp-{unique_topic}")
                .auto_offset_reset("earliest")
                .build()
            )
            with KafkaConsumer(cons_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.value_as_json() == {"compressed": True}
        finally:
            admin.delete_topic(unique_topic)

    def test_producer_config_with_acks(self, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.config import ProducerConfig

        config = (
            ProducerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .acks("all")
            .build()
        )

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(config) as producer:
                producer.send(unique_topic, b"acks=all message")
                producer.flush()
        finally:
            admin.delete_topic(unique_topic)

    def test_producer_idempotent_config(self, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.config import ProducerConfig

        config = (
            ProducerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .enable_idempotence()
            .build()
        )

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(config) as producer:
                producer.send(unique_topic, b"idempotent")
                producer.flush()
        finally:
            admin.delete_topic(unique_topic)

    def test_config_validation_passes(self):
        from typedkafka.config import ProducerConfig

        config = (
            ProducerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .enable_idempotence()
            .acks("all")
            .build(validate=True)
        )
        assert config["enable.idempotence"] is True
        assert config["acks"] == "all"

    def test_producer_config_set_custom(self, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.config import ProducerConfig

        config = (
            ProducerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .set("linger.ms", 10)
            .set("batch.size", 32768)
            .build()
        )

        admin = KafkaAdmin({"bootstrap.servers": KAFKA_BOOTSTRAP})
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(config) as producer:
                producer.send(unique_topic, b"custom config")
                producer.flush()
        finally:
            admin.delete_topic(unique_topic)

    def test_security_config_methods(self):
        """Test that security config builder methods produce valid dicts."""
        from typedkafka.config import ProducerConfig

        config = (
            ProducerConfig()
            .bootstrap_servers(KAFKA_BOOTSTRAP)
            .sasl_plain("user", "pass")
            .build()
        )
        assert config["sasl.username"] == "user"
        assert config["sasl.password"] == "pass"
        assert config["sasl.mechanisms"] == "PLAIN"
        assert config["security.protocol"] == "SASL_PLAINTEXT"
