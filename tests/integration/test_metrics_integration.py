"""Integration tests for metrics with a real broker."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestMetricsIntegration:
    """Test metrics collection against a real broker."""

    def test_producer_metrics_tracking(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                assert producer.metrics.messages_sent == 0
                producer.send(unique_topic, b"msg1")
                producer.send(unique_topic, b"msg2")
                producer.send(unique_topic, b"msg3")
                producer.flush()
                assert producer.metrics.messages_sent == 3
                assert producer.metrics.errors == 0
        finally:
            admin.delete_topic(unique_topic)

    def test_consumer_metrics_tracking(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                for i in range(5):
                    producer.send(unique_topic, f"msg{i}".encode())
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                for _ in range(20):
                    consumer.poll(timeout=2.0)
                    if consumer.metrics.messages_received >= 5:
                        break

                assert consumer.metrics.messages_received >= 5
                assert consumer.metrics.errors == 0
        finally:
            admin.delete_topic(unique_topic)

    def test_producer_stats_callback(self, producer_config, unique_topic):
        """Test on_stats callback fires with KafkaStats."""
        import time

        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.metrics import KafkaStats

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        stats_received: list[KafkaStats] = []

        def on_stats(stats: KafkaStats) -> None:
            stats_received.append(stats)

        producer_config["statistics.interval.ms"] = 1000

        try:
            with KafkaProducer(producer_config, on_stats=on_stats) as producer:
                producer.send(unique_topic, b"trigger stats")
                producer.flush()
                # Wait for stats callback to fire
                for _ in range(10):
                    producer._producer.poll(500)
                    time.sleep(0.5)
                    if stats_received:
                        break

            assert len(stats_received) >= 1
            stats = stats_received[0]
            assert isinstance(stats, KafkaStats)
            assert isinstance(stats.raw, dict)
        finally:
            admin.delete_topic(unique_topic)

    def test_consumer_stats_callback(self, producer_config, consumer_config, unique_topic):
        """Test consumer on_stats callback."""
        import time

        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.metrics import KafkaStats

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        stats_received: list[KafkaStats] = []

        def on_stats(stats: KafkaStats) -> None:
            stats_received.append(stats)

        consumer_config["statistics.interval.ms"] = 1000

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, b"msg")
                producer.flush()

            with KafkaConsumer(consumer_config, on_stats=on_stats) as consumer:
                consumer.subscribe([unique_topic])
                for _ in range(10):
                    consumer.poll(timeout=1.0)
                    time.sleep(0.5)
                    if stats_received:
                        break

            assert len(stats_received) >= 1
            assert isinstance(stats_received[0], KafkaStats)
        finally:
            admin.delete_topic(unique_topic)
