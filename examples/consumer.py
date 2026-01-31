"""Basic consumer usage."""

from typedkafka import KafkaConsumer

config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-consumer-group",
    "auto.offset.reset": "earliest",
}

with KafkaConsumer(config) as consumer:
    consumer.subscribe(["my-topic"])
    for msg in consumer:
        data = msg.value_as_json()
        print(f"Received: {data}")
        consumer.commit(msg)
