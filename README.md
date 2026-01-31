# typedkafka

A well-documented, fully type-hinted Kafka client for Python.

[![Python Version](https://img.shields.io/pypi/pyversions/typedkafka)](https://pypi.org/project/typedkafka/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

Existing Python Kafka libraries have limited documentation and type hints:

- **confluent-kafka**: Powerful CPython wrapper around librdkafka, but minimal docstrings and no type hints
- **kafka-python**: Unmaintained since 2020, lacks comprehensive documentation

Developers are forced to:
- Constantly reference external documentation
- Miss IDE autocomplete benefits
- Guess at parameter types and return values
- Deal with cryptic error messages

**typedkafka solves this** with a modern, well-documented wrapper that provides excellent developer experience.

## Installation

```bash
pip install typedkafka
```

Requires Python 3.9+ and installs `confluent-kafka` as a dependency.

## Quick Start

### Producer

```python
from typedkafka import KafkaProducer

# Create a producer with context manager (automatic cleanup)
with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    # Send bytes
    producer.send("my-topic", b"Hello, Kafka!")

    # Send JSON (automatic serialization)
    producer.send_json("events", {"user_id": 123, "action": "click"})

    # Send string
    producer.send_string("logs", "Application started")

    # Wait for all messages to be delivered
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

# Iterate over messages with context manager
with KafkaConsumer(config) as consumer:
    consumer.subscribe(["my-topic"])

    for msg in consumer:
        # Access message data with type-safe methods
        print(f"Topic: {msg.topic}")
        print(f"Partition: {msg.partition}")
        print(f"Offset: {msg.offset}")

        # Convenient deserialization
        text = msg.value_as_string()
        data = msg.value_as_json()

        # Manual commit
        consumer.commit(msg)
```

## Features

### 1. Comprehensive Documentation

Every class, method, and parameter is documented with:
- Clear descriptions
- Parameter types and meanings
- Return value descriptions
- Common configuration options
- Real-world examples
- Error conditions

**Example:** The `send()` method documents all parameters:

```python
def send(
    self,
    topic: str,           # The topic name - fully documented
    value: bytes,         # Message payload - type hints show it's bytes
    key: Optional[bytes] = None,  # Optional key for partitioning
    partition: Optional[int] = None,  # Target partition (optional)
    on_delivery: Optional[Callable] = None,  # Delivery callback
) -> None:
    """
    Send a message to a Kafka topic.

    This method is asynchronous - it returns immediately after queuing.
    Use flush() to wait for delivery confirmation.

    Args:
        topic: The topic name to send the message to
        value: The message payload as bytes
        key: Optional message key as bytes. Messages with the same
             key go to the same partition.
        partition: Optional partition number. If None, partition is
                  chosen by the partitioner.
        on_delivery: Optional callback function called when delivery
                    succeeds or fails. Signature: callback(error, message)

    Raises:
        ProducerError: If the message cannot be queued (e.g., queue is full)

    Examples:
        >>> # Send a simple message
        >>> producer.send("my-topic", b"Hello, Kafka!")

        >>> # Send with a key for partitioning
        >>> producer.send("user-events", b"event data", key=b"user-123")
    """
```

### 2. Full Type Hints

Get IDE autocomplete and type checking for all methods:

```python
from typedkafka import KafkaProducer, KafkaConsumer, KafkaMessage

# IDE knows the types
producer: KafkaProducer = KafkaProducer(config)
message: KafkaMessage = consumer.poll()
value: bytes = message.value
text: str = message.value_as_string()  # Type-safe deserialization
```

### 3. Better Error Messages

Clear, actionable error messages with context:

```python
from typedkafka import ProducerError, ConsumerError, SerializationError

try:
    producer.send_json("topic", non_serializable_object)
except SerializationError as e:
    # Error includes the value that failed and the original error
    print(f"Failed to serialize: {e}")
    print(f"Problematic value: {e.value}")
    print(f"Original error: {e.original_error}")
```

### 4. Convenient Helper Methods

#### JSON Support

```python
# Producer
producer.send_json("events", {"user_id": 123, "action": "click"})

# Consumer
msg = consumer.poll()
data = msg.value_as_json()  # Automatic deserialization
print(f"User: {data['user_id']}")
```

#### String Support

```python
# Producer
producer.send_string("logs", "Application error occurred")

# Consumer
msg = consumer.poll()
log_message = msg.value_as_string()
```

#### Message Key Helpers

```python
msg = consumer.poll()
if msg.key:
    key_str = msg.key_as_string()
    print(f"Key: {key_str}")
```

### 5. Context Manager Support

Automatic resource cleanup:

```python
with KafkaProducer(config) as producer:
    producer.send("topic", b"message")
    # Automatic flush() and cleanup on exit

with KafkaConsumer(config) as consumer:
    consumer.subscribe(["topic"])
    for msg in consumer:
        process(msg)
    # Automatic close() on exit
```

### 6. Iterator Protocol

Consume messages pythonically:

```python
for msg in consumer:
    print(f"Received: {msg.value_as_string()}")
    consumer.commit(msg)
```

## Configuration Examples

### Producer Configuration

```python
producer = KafkaProducer({
    # Required
    "bootstrap.servers": "broker1:9092,broker2:9092",

    # Optional but recommended
    "client.id": "my-app-producer",
    "acks": "all",  # Wait for all replicas
    "compression.type": "gzip",  # Compress messages
    "max.in.flight.requests.per.connection": 5,
    "linger.ms": 10,  # Wait up to 10ms to batch messages
    "batch.size": 16384,  # 16KB batch size
})
```

### Consumer Configuration

```python
consumer = KafkaConsumer({
    # Required
    "bootstrap.servers": "broker1:9092,broker2:9092",
    "group.id": "my-consumer-group",

    # Optional but recommended
    "client.id": "my-app-consumer",
    "auto.offset.reset": "earliest",  # Start from beginning if no offset
    "enable.auto.commit": False,  # Manual offset management
    "max.poll.interval.ms": 300000,  # 5 minutes
    "session.timeout.ms": 10000,  # 10 seconds
})
```

## Real-World Examples

### Async Message Production with Callbacks

```python
delivered_count = 0
failed_count = 0

def on_delivery(err, msg):
    global delivered_count, failed_count
    if err:
        failed_count += 1
        print(f"Delivery failed: {err}")
    else:
        delivered_count += 1

with KafkaProducer(config) as producer:
    for i in range(1000):
        producer.send_json(
            "events",
            {"id": i, "timestamp": time.time()},
            on_delivery=on_delivery
        )

    producer.flush()
    print(f"Delivered: {delivered_count}, Failed: {failed_count}")
```

### Consumer with Error Handling

```python
from typedkafka import KafkaConsumer, ConsumerError, SerializationError

with KafkaConsumer(config) as consumer:
    consumer.subscribe(["events"])

    for msg in consumer:
        try:
            data = msg.value_as_json()
            process_event(data)
            consumer.commit(msg)
        except SerializationError as e:
            # Log malformed message
            logger.error(f"Malformed message at offset {msg.offset}: {e}")
            # Skip and commit to move forward
            consumer.commit(msg)
        except Exception as e:
            # Processing error - don't commit, will retry
            logger.error(f"Processing error: {e}")
            break
```

### Manual Offset Management

```python
consumer = KafkaConsumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-group",
    "enable.auto.commit": False  # Manual commits
})

consumer.subscribe(["orders"])

while True:
    msg = consumer.poll(timeout=1.0)
    if msg:
        try:
            order = msg.value_as_json()
            process_order(order)

            # Only commit after successful processing
            consumer.commit(msg, asynchronous=False)  # Synchronous commit
        except Exception as e:
            logger.error(f"Failed to process order: {e}")
            # Don't commit - will reprocess on restart
```

## Why typedkafka Over Alternatives?

| Feature | typedkafka | confluent-kafka | kafka-python |
|---------|-----------|-----------------|--------------|
| Type hints | ✅ Full | ❌ None | ❌ None |
| Docstrings | ✅ Comprehensive | ⚠️ Minimal | ⚠️ Minimal |
| Performance | ✅ (uses confluent-kafka) | ✅ Fast (C lib) | ⚠️ Pure Python |
| Maintenance | ✅ Active | ✅ Active | ❌ Unmaintained |
| Python 3.9+ | ✅ Yes | ✅ Yes | ⚠️ Old Python |
| Context managers | ✅ Yes | ⚠️ Manual | ⚠️ Manual |
| JSON helpers | ✅ Built-in | ❌ Manual | ❌ Manual |
| Error messages | ✅ Detailed | ⚠️ Cryptic | ⚠️ Cryptic |
| IDE autocomplete | ✅ Excellent | ❌ Limited | ❌ Limited |

**typedkafka** is built on top of `confluent-kafka`, giving you the same performance and reliability with dramatically better developer experience.

## Development

```bash
# Clone the repository
git clone https://github.com/Jgprog117/typedkafka.git
cd typedkafka

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Run linter
ruff check .

# Run type checker
mypy src
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Changelog

### 0.1.0 (2026-01-31)

- Initial release
- Comprehensive documentation for all classes and methods
- Full type hints throughout
- KafkaProducer with send, send_json, send_string methods
- KafkaConsumer with poll, subscribe, commit methods
- KafkaMessage with value_as_json, value_as_string helper methods
- Context manager support for automatic cleanup
- Iterator protocol for easy message consumption
- Better error messages with context
- Zero additional dependencies beyond confluent-kafka
