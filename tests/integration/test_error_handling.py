"""Integration tests for error handling and exception context."""

from __future__ import annotations

import pytest

from tests.integration.conftest import integration


@integration
class TestErrorHandlingIntegration:
    """Test error handling with a real broker."""

    def test_serialization_error_on_bad_json(self, producer_config, unique_topic):
        """send_json raises SerializationError for non-serializable objects."""
        from typedkafka import KafkaProducer
        from typedkafka.exceptions import SerializationError

        with KafkaProducer(producer_config) as producer:
            with pytest.raises(SerializationError):
                producer.send_json(unique_topic, object())

    def test_producer_error_context(self, producer_config, unique_topic):
        """ProducerError includes useful context."""
        from typedkafka import KafkaProducer
        from typedkafka.exceptions import SerializationError

        with KafkaProducer(producer_config) as producer:
            try:
                producer.send_json(unique_topic, object())
            except SerializationError as e:
                assert "JSON" in str(e)
                assert e.original_error is not None

    def test_commit_without_subscription(self, consumer_config):
        """Committing without an active subscription raises ConsumerError."""
        from typedkafka import KafkaConsumer
        from typedkafka.exceptions import ConsumerError

        with KafkaConsumer(consumer_config) as consumer:
            with pytest.raises(ConsumerError):
                consumer.commit(asynchronous=False)

    def test_transaction_abort_on_exception(self, producer_config, consumer_config, unique_topic):
        """Transaction aborts when exception is raised inside context manager."""
        import time

        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        producer_config["transactional.id"] = f"test-abort-{unique_topic}"
        producer_config["enable.idempotence"] = True
        producer_config["transaction.timeout.ms"] = 60000

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        time.sleep(2)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.init_transactions(timeout=60)

                # This transaction should abort
                with pytest.raises(ValueError):
                    with producer.transaction():
                        producer.send_json(unique_topic, {"should": "abort"})
                        raise ValueError("intentional")

            # Verify message was NOT committed (read_committed consumer)
            consumer_config["isolation.level"] = "read_committed"
            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=5.0)
                assert msg is None
        finally:
            admin.delete_topic(unique_topic)

    def test_configuration_error(self):
        """ConfigurationError raised for invalid config combinations."""
        from typedkafka.config import ProducerConfig
        from typedkafka.exceptions import ConfigurationError

        config = ProducerConfig().bootstrap_servers("localhost:9092")
        config = config.transactional_id("my-txn")
        # transactional.id without idempotence should fail validation
        with pytest.raises(ConfigurationError):
            config.build(validate=True)

    def test_kafka_error_context_dataclass(self):
        """KafkaErrorContext holds structured error data."""
        from typedkafka.exceptions import KafkaErrorContext

        ctx = KafkaErrorContext(topic="my-topic", partition=0, offset=42)
        assert ctx.topic == "my-topic"
        assert ctx.partition == 0
        assert ctx.offset == 42
        ctx_str = str(ctx)
        assert "my-topic" in ctx_str

    def test_transaction_error_type(self, producer_config):
        """TransactionError is raised for transaction failures."""
        from typedkafka import KafkaProducer
        from typedkafka.exceptions import TransactionError

        # init_transactions without transactional.id should fail
        with KafkaProducer(producer_config) as producer:
            with pytest.raises(TransactionError):
                producer.init_transactions()
