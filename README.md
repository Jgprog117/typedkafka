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
- Metrics collection and statistics tracking (`KafkaMetrics`, `KafkaStats`)
- Dead letter queue helper (`DeadLetterQueue`, `process_with_dlq`)
- Message headers support on `send()`
- Testing utilities (MockProducer/MockConsumer/MockDeadLetterQueue) with full API parity
- Type-safe configuration builders with validation and security helpers (SASL, SSL)
- Admin client for topic management
- Batch polling and consumer offset management (seek, assign, position)

## Why typedkafka?

confluent-kafka is fast and reliable, but working with it in Python often means guessing at argument types, cross-referencing C library docs, and getting cryptic error messages. typedkafka fixes that:

- **IDE autocomplete that works** — full type hints and parameter docs on every method, so you're not guessing at argument types or return values
- **Clear error messages** — a proper exception hierarchy instead of cryptic confluent-kafka errors
- **Test without a broker** — MockProducer and MockConsumer let you write unit tests without Docker or flaky integration setups
- **Less boilerplate** — transactions, async, retry, and serialization are built in instead of requiring manual wiring

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

### Configuration Builders

```python
from typedkafka import ProducerConfig, KafkaProducer

config = (
    ProducerConfig()
    .bootstrap_servers("broker:9093")
    .sasl_scram("user", "password")
    .acks("all")
    .compression("gzip")
    .build(validate=True)
)

producer = KafkaProducer(config)
```

See the [`examples/`](examples/) directory for more: transactions, async, retry, serializers, batch send, testing mocks, config builders, metrics, and dead letter queues.

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

See [CHANGELOG.md](CHANGELOG.md) for the full release history.
