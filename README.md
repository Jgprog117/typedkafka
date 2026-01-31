# typedkafka

A well-documented, fully type-hinted Kafka client for Python.

[![Python Version](https://img.shields.io/pypi/pyversions/typedkafka)](https://pypi.org/project/typedkafka/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

typedkafka provides a modern Python interface to Apache Kafka with comprehensive documentation, full type hints, and developer-friendly features. Built on confluent-kafka for performance and reliability.

**Key Features:**
- Comprehensive docstrings for every class and method
- Full type hints for IDE autocomplete and type checking
- Convenient helper methods for JSON and string messages
- Testing utilities (MockProducer/MockConsumer) for unit tests
- Type-safe configuration builders
- Admin client for topic management
- Context managers for automatic resource cleanup

## Installation

```bash
pip install typedkafka
```

Requires Python 3.9+ and installs `confluent-kafka` as a dependency.

## Quick Start

### Producer

```python
from typedkafka import KafkaProducer

with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    # Send bytes
    producer.send("my-topic", b"Hello, Kafka!")

    # Send JSON (automatic serialization)
    producer.send_json("events", {"user_id": 123, "action": "click"})

    # Send string
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
        # Convenient deserialization
        data = msg.value_as_json()
        print(f"Received: {data}")

        consumer.commit(msg)
```

## Testing Utilities

Mock implementations for testing without running Kafka:

```python
from typedkafka.testing import MockProducer, MockConsumer

def test_my_function():
    producer = MockProducer()
    my_function(producer)

    # Verify what was sent
    assert len(producer.messages["events"]) == 1
    msg = producer.messages["events"][0]
    assert msg.value == b"expected"

def test_message_processing():
    consumer = MockConsumer()
    consumer.add_json_message("events", {"user_id": 123})

    result = process_messages(consumer)
    assert result is not None
```

## Type-Safe Configuration

Fluent builders with IDE autocomplete:

```python
from typedkafka import ProducerConfig, KafkaProducer

config = (ProducerConfig()
    .bootstrap_servers("localhost:9092")
    .acks("all")
    .compression("gzip")
    .linger_ms(10)
    .build())

producer = KafkaProducer(config)
```

## Admin Operations

Manage topics and cluster configuration:

```python
from typedkafka import KafkaAdmin

admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})

# Create topic
admin.create_topic("events", num_partitions=10, replication_factor=3)

# List topics
topics = admin.list_topics()

# Get topic details
info = admin.describe_topic("events")

# Delete topic
admin.delete_topic("old-topic")
```

## Comprehensive Documentation

Every method includes detailed documentation:

```python
def send(
    self,
    topic: str,
    value: bytes,
    key: Optional[bytes] = None,
    partition: Optional[int] = None,
    on_delivery: Optional[Callable] = None,
) -> None:
    """
    Send a message to a Kafka topic.

    This method is asynchronous - returns immediately after queuing.
    Use flush() to wait for delivery confirmation.

    Args:
        topic: The topic name to send the message to
        value: The message payload as bytes
        key: Optional message key as bytes. Messages with the same
             key go to the same partition.
        partition: Optional partition number. If None, partition is
                  chosen by the partitioner.
        on_delivery: Optional callback function called when delivery
                    succeeds or fails.

    Raises:
        ProducerError: If the message cannot be queued

    Examples:
        >>> producer.send("my-topic", b"Hello!")
        >>> producer.send("events", b"data", key=b"user-123")
    """
```

## Better Error Messages

Clear, actionable errors with context:

```python
try:
    producer.send_json("topic", non_serializable_object)
except SerializationError as e:
    # Error includes:
    # - Clear message
    # - The problematic value (e.value)
    # - Original error (e.original_error)
    print(f"Failed to serialize: {e}")
```

## Development

```bash
# Clone the repository
git clone https://github.com/Jgprog117/typedkafka.git
cd typedkafka

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .
```

## License

MIT License - see LICENSE file for details.

## Changelog

### 0.2.0 (2026-01-31)

- Added testing utilities (MockProducer, MockConsumer)
- Added type-safe configuration builders (ProducerConfig, ConsumerConfig)
- Added Admin client wrapper for topic management
- Improved documentation and examples

### 0.1.0 (2026-01-31)

- Initial release
- KafkaProducer with comprehensive documentation
- KafkaConsumer with helper methods
- Full type hints throughout
- Context manager support
- JSON and string convenience methods
