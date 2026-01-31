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

### 0.3.2

- Move code examples from README into standalone `examples/` directory
- Pin all CI/CD actions to commit SHAs for supply chain security
- Switch PyPI publishing to Trusted Publishers (OIDC) instead of API tokens
- Add `py.typed` marker file for PEP 561 compliance

### 0.3.1

- Update README, CONTRIBUTING, and SECURITY docs for v0.3.0 features

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
