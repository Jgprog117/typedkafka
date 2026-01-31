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

See the [`examples/`](examples/) directory for more: transactions, async, retry, serializers, batch send, testing mocks, and config builders.

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
