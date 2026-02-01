"""Async producer and consumer with batch consumption."""

import asyncio

from typedkafka.aio import AsyncKafkaConsumer, AsyncKafkaProducer, MessageBatch, batch_consume


async def main():
    # Async producer
    async with AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
        await producer.send("topic", b"async message")
        await producer.send_json("events", {"id": 1})

        # v0.6.0: send_string convenience method
        await producer.send_string("greetings", "hello from async")

        await producer.flush()

    # Async consumer
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "my-group",
        "auto.offset.reset": "earliest",
    }
    async with AsyncKafkaConsumer(config) as consumer:
        consumer.subscribe(["topic"])

        # Iterate over individual messages
        async for msg in consumer:
            print(msg.value_as_json())
            break  # just one for demo

    # v0.6.0: Batch consumption with MessageBatch
    async with AsyncKafkaConsumer(config) as consumer:
        consumer.subscribe(["events"])
        async for batch in batch_consume(consumer, batch_size=50, batch_timeout=2.0):
            assert isinstance(batch, MessageBatch)
            print(f"Received batch of {len(batch.messages)} messages")
            for msg in batch.messages:
                print(f"  offset={msg.offset}, value={msg.value}")
            break  # just one batch for demo


if __name__ == "__main__":
    asyncio.run(main())
