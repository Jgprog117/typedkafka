"""Integration tests requiring a real Kafka broker.

Run with: KAFKA_BOOTSTRAP_SERVERS=localhost:9092 pytest tests/integration -v
"""

import time

from tests.integration.conftest import integration


@integration
class TestProducerConsumerIntegration:
    """Integration tests requiring a real Kafka broker."""

    def test_produce_and_consume(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_json(unique_topic, {"test": "data"})
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=10.0)

                assert msg is not None
                assert msg.value_as_json() == {"test": "data"}
        finally:
            admin.delete_topic(unique_topic)

    def test_produce_string_and_consume(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_string(unique_topic, "hello world")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=10.0)

                assert msg is not None
                assert msg.value_as_string() == "hello world"
        finally:
            admin.delete_topic(unique_topic)

    def test_transaction(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        producer_config["transactional.id"] = f"test-txn-{unique_topic}"
        producer_config["enable.idempotence"] = True
        producer_config["transaction.timeout.ms"] = 60000

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        # Allow topic metadata to propagate before starting transactions
        time.sleep(2)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.init_transactions(timeout=60)

                with producer.transaction():
                    producer.send_json(unique_topic, {"txn": "message"})

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = consumer.poll(timeout=10.0)
                assert msg is not None
                assert msg.value_as_json() == {"txn": "message"}
        finally:
            admin.delete_topic(unique_topic)
