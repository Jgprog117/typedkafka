"""Retry utilities with exponential backoff."""

from typedkafka import KafkaProducer
from typedkafka.retry import RetryPolicy, retry


# Decorator-based retry
@retry(max_attempts=3, backoff_base=1.0)
def send_with_retry(producer, data):
    producer.send_json("events", data)
    producer.flush()


# Programmatic retry via RetryPolicy
producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
policy = RetryPolicy(max_attempts=5, backoff_base=0.5)
policy.execute(producer.send, "topic", b"value")
