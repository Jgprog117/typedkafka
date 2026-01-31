"""Batch send multiple messages."""

from typedkafka import KafkaProducer

with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    producer.send_batch("events", [
        (b"event1", b"key1"),
        (b"event2", b"key2"),
        (b"event3", None),
    ])
    producer.flush()
