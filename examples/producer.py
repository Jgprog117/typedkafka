"""Basic producer usage."""

from typedkafka import KafkaProducer

with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    # Send raw bytes
    producer.send("my-topic", b"Hello, Kafka!")

    # Send JSON (automatically serialized)
    producer.send_json("events", {"user_id": 123, "action": "click"})

    # Send a string
    producer.send_string("logs", "Application started")

    producer.flush()
