"""Integration tests for retry utilities with real Kafka operations."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestRetryIntegration:
    """Test retry decorator with real broker operations."""

    def test_retry_on_transient_failure(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.retry import retry

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        attempts = []

        @retry(max_attempts=3, backoff_base=0.1, retryable_exceptions=(ValueError,))
        def produce_with_retry():
            attempts.append(1)
            if len(attempts) < 2:
                raise ValueError("transient error")
            with KafkaProducer(producer_config) as producer:
                producer.send_json(unique_topic, {"retried": True})
                producer.flush()

        try:
            produce_with_retry()
            assert len(attempts) == 2  # failed once, succeeded on retry

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.value_as_json() == {"retried": True}
        finally:
            admin.delete_topic(unique_topic)

    def test_retry_policy_execute(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.retry import RetryPolicy

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base=0.1,
            retryable_exceptions=(ValueError,),
        )

        call_count = 0

        def flaky_produce():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("flaky")
            with KafkaProducer(producer_config) as producer:
                producer.send_string(unique_topic, "retry-policy")
                producer.flush()

        try:
            policy.execute(flaky_produce)
            assert call_count == 2
        finally:
            admin.delete_topic(unique_topic)
