# typedkafka

A well-documented, fully type-hinted Kafka client for Python.

[![Python Version](https://img.shields.io/pypi/pyversions/typedkafka)](https://pypi.org/project/typedkafka/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

typedkafka provides a modern Python interface to Apache Kafka with comprehensive documentation, full type hints, and developer-friendly features. Built on confluent-kafka for performance and reliability.

**Key Features:**
- Full type hints and comprehensive docstrings
- JSON, string, and bytes message helpers
- Transaction support with context managers
- Async producer and consumer (`asyncio`)
- Retry utilities with exponential backoff
- Pluggable serializer framework (JSON, String, Avro/Schema Registry)
- Testing utilities (MockProducer/MockConsumer)
- Type-safe configuration builders with validation
- Admin client for topic management

## Installation

```bash
pip install typedkafka

# With Avro/Schema Registry support
pip install typedkafka[avro]
```

Requires Python 3.9+.

## Quick Start

### Producer

```python
from typedkafka import KafkaProducer

with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    producer.send("my-topic", b"Hello, Kafka!")
    producer.send_json("events", {"user_id": 123, "action": "click"})
    producer.send_string("logs", "Application started")
    producer.flush()
```

### Consumer

```python
from typedkafka import KafkaConsumer

config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-consumer-group",
    "auto.offset.reset": "earliest"
}

with KafkaConsumer(config) as consumer:
    consumer.subscribe(["my-topic"])
    for msg in consumer:
        data = msg.value_as_json()
        print(f"Received: {data}")
        consumer.commit(msg)
```

### Transactions

```python
from typedkafka import KafkaProducer

producer = KafkaProducer({
    "bootstrap.servers": "localhost:9092",
    "transactional.id": "my-txn-id",
})
producer.init_transactions()

with producer.transaction():
    producer.send("topic", b"msg1")
    producer.send("topic", b"msg2")
    # Commits on success, aborts on exception
```

### Async

```python
from typedkafka.aio import AsyncKafkaProducer, AsyncKafkaConsumer

async with AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    await producer.send("topic", b"async message")
    await producer.send_json("events", {"id": 1})
    await producer.flush()

async with AsyncKafkaConsumer(config) as consumer:
    consumer.subscribe(["topic"])
    async for msg in consumer:
        process(msg)
```

### Retry

```python
from typedkafka.retry import retry, RetryPolicy

@retry(max_attempts=3, backoff_base=1.0)
def send_with_retry(producer, data):
    producer.send_json("events", data)
    producer.flush()

# Or use RetryPolicy programmatically
policy = RetryPolicy(max_attempts=5, backoff_base=0.5)
policy.execute(producer.send, "topic", b"value")
```

### Serializers

```python
from typedkafka.serializers import JsonSerializer, AvroSerializer

json_ser = JsonSerializer()
data = json_ser.serialize("topic", {"user_id": 123})

# Avro with Schema Registry (requires typedkafka[avro])
avro_ser = AvroSerializer("http://localhost:8081", schema_str)
data = avro_ser.serialize("users", {"id": 123, "name": "Alice"})
```

### Batch Send

```python
producer.send_batch("events", [
    (b"event1", b"key1"),
    (b"event2", b"key2"),
    (b"event3", None),
])
producer.flush()
```

## Testing Utilities

Mock implementations for testing without a running Kafka broker:

```python
from typedkafka.testing import MockProducer, MockConsumer

def test_my_producer():
    producer = MockProducer()
    my_function(producer)
    assert len(producer.messages["events"]) == 1

def test_my_consumer():
    consumer = MockConsumer()
    consumer.add_json_message("events", {"user_id": 123})
    result = process_messages(consumer)
    assert result is not None

def test_transactions():
    producer = MockProducer()
    producer.init_transactions()
    with producer.transaction():
        producer.send("topic", b"transactional msg")
    assert len(producer.messages["topic"]) == 1
```

## Type-Safe Configuration

Fluent builders with validation and IDE autocomplete:

```python
from typedkafka import ProducerConfig, ConsumerConfig, KafkaProducer

config = (ProducerConfig()
    .bootstrap_servers("localhost:9092")
    .acks("all")
    .compression("gzip")
    .linger_ms(10)
    .build())

producer = KafkaProducer(config)
```

Invalid values raise `ValueError` immediately:

```python
ProducerConfig().acks("invalid")      # ValueError
ProducerConfig().compression("brotli") # ValueError
```

## Development

```bash
git clone https://github.com/Jgprog117/typedkafka.git
cd typedkafka
pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

## License

MIT License - see LICENSE file for details.

## Changelog

### 0.3.0

- Transaction support: `init_transactions()`, `begin/commit/abort_transaction()`, `transaction()` context manager
- Async producer and consumer (`typedkafka.aio`)
- Retry utilities: `@retry` decorator and `RetryPolicy` class
- Pluggable serializers: `Serializer`/`Deserializer` ABCs, JSON, String, and Avro implementations
- Batch send: `send_batch()` on producer
- Consumer rebalance callbacks: `on_assign`, `on_revoke`, `on_lost` on `subscribe()`
- Configurable iterator poll timeout via `poll_timeout` attribute
- Config validation: early `ValueError` on invalid `acks`, `compression`, `auto_offset_reset`, `linger_ms`, `batch_size`
- Expanded test suite (120 tests)

### 0.2.0

- Testing utilities (MockProducer, MockConsumer)
- Type-safe configuration builders (ProducerConfig, ConsumerConfig)
- Admin client wrapper for topic management

### 0.1.0

- Initial release with KafkaProducer, KafkaConsumer, full type hints, context manager support
