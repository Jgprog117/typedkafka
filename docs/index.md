# typedkafka

A well-documented, fully type-hinted Kafka client for Python.

Built on [confluent-kafka](https://github.com/confluentinc/confluent-kafka-python) for performance and reliability.

## Features

- **Full type hints** and comprehensive docstrings on every public API
- **JSON, string, and bytes** message helpers
- **Transaction support** with context managers
- **Async producer and consumer** via `asyncio`
- **Retry utilities** with exponential backoff
- **Pluggable serializers** (JSON, String, Avro/Schema Registry)
- **Metrics collection** and statistics tracking (`KafkaMetrics`, `KafkaStats`)
- **Dead letter queue** helper (`DeadLetterQueue`, `process_with_dlq`)
- **Message headers** support on `send()`
- **Testing utilities** (MockProducer/MockConsumer/MockDeadLetterQueue) with full API parity
- **Type-safe config builders** with validation and security helpers (SASL, SSL)
- **Admin client** for topic management
- **Batch polling** and consumer offset management (seek, assign, position)

## Installation

```bash
pip install typedkafka

# With Avro/Schema Registry support
pip install typedkafka[avro]
```

Requires Python 3.9+.

## Quick Start

```python
from typedkafka import KafkaProducer

with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    producer.send("my-topic", b"Hello, Kafka!")
    producer.send_json("events", {"user_id": 123, "action": "click"})
    producer.flush()
```

```python
from typedkafka import KafkaConsumer

with KafkaConsumer({"bootstrap.servers": "localhost:9092", "group.id": "my-group"}) as consumer:
    consumer.subscribe(["my-topic"])
    for msg in consumer:
        print(msg.value_as_json())
        consumer.commit(msg)
```

See the [Getting Started](getting-started.md) guide for more examples.
