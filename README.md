# typedkafka

A well-documented, fully type-hinted Kafka client for Python.

[![Python Version](https://img.shields.io/pypi/pyversions/typedkafka)](https://pypi.org/project/typedkafka/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

typedkafka provides a modern Python interface to Apache Kafka with comprehensive documentation, full type hints, and developer-friendly features. Built on confluent-kafka for performance and reliability.

**Key Features:**
- Full type hints and IDE autocomplete on every public method
- Type-safe topics with generic serialization/deserialization
- Transactions, async, retry, and batch operations built in
- Pluggable serializers: JSON, string, Protobuf, Avro/Schema Registry
- Structured logging, metrics, OpenTelemetry tracing, and dead letter queues
- Testing mocks with full API parity — no broker needed for unit tests
- Type-safe config builders with presets, validation, and security helpers

## Why typedkafka?

confluent-kafka is fast and reliable, but its Python API lacks type hints, has sparse docs, and surfaces raw C-level errors. typedkafka wraps it with a modern, Pythonic interface:

- **Type safety** — full type hints, generic `TypedTopic[T]`, and IDE autocomplete so you catch mistakes before runtime
- **Batteries included** — transactions, async, retry, serialization, logging, metrics, and dead letter queues out of the box
- **Testable** — mock producer/consumer with full API parity; write unit tests without Docker
- **Observable** — structured logging, OpenTelemetry tracing, and metrics collection built in

## Installation

```bash
pip install typedkafka

# With Avro/Schema Registry support
pip install typedkafka[avro]

# With Protobuf support
pip install typedkafka[protobuf]

# Everything
pip install typedkafka[all]
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
