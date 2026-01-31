"""Async producer and consumer."""

import asyncio

from typedkafka.aio import AsyncKafkaConsumer, AsyncKafkaProducer


async def main():
    # Async producer
    async with AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
        await producer.send("topic", b"async message")
        await producer.send_json("events", {"id": 1})
        await producer.flush()

    # Async consumer
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "my-group",
        "auto.offset.reset": "earliest",
    }
    async with AsyncKafkaConsumer(config) as consumer:
        consumer.subscribe(["topic"])
        async for msg in consumer:
            print(msg.value())


if __name__ == "__main__":
    asyncio.run(main())
