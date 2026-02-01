# Cookbook

Practical recipes and patterns for common Kafka use cases.

## Exactly-Once Processing

The read-process-write pattern using transactions for exactly-once semantics.

```python
from typedkafka import KafkaConsumer, KafkaProducer

producer = KafkaProducer({
    "bootstrap.servers": "localhost:9092",
    "transactional.id": "my-processor-1",
})
producer.init_transactions()

consumer = KafkaConsumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "processor-group",
    "isolation.level": "read_committed",
    "enable.auto.commit": False,
})
consumer.subscribe(["input-topic"])

for msg in consumer:
    with producer.transaction():
        data = msg.value_as_json()
        result = transform(data)
        producer.send_json("output-topic", result)
        # Commit input offset within the same transaction
        producer._producer.send_offsets_to_transaction(
            consumer._consumer.position(consumer._consumer.assignment()),
            consumer._consumer.consumer_group_metadata(),
        )
```

## Fan-Out Pattern

Send one event to multiple topics atomically using transactions.

```python
from typedkafka import KafkaProducer

producer = KafkaProducer({
    "bootstrap.servers": "localhost:9092",
    "transactional.id": "fan-out",
})
producer.init_transactions()

event = {"user_id": 123, "action": "purchase", "amount": 99.99}

with producer.transaction():
    producer.send_json("analytics-events", event)
    producer.send_json("billing-events", {
        "user_id": event["user_id"],
        "amount": event["amount"],
    })
    producer.send_json("notifications", {
        "user_id": event["user_id"],
        "message": f"Purchase of ${event['amount']} confirmed",
    })
# All three succeed or all fail together
```

## Graceful Shutdown

Handle signals and flush pending messages on shutdown.

```python
import signal
from typedkafka import KafkaProducer, KafkaConsumer

shutdown = False

def on_signal(sig, frame):
    global shutdown
    shutdown = True

signal.signal(signal.SIGINT, on_signal)
signal.signal(signal.SIGTERM, on_signal)

producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
consumer = KafkaConsumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-group",
    "enable.auto.commit": False,
})
consumer.subscribe(["events"])

try:
    while not shutdown:
        msg = consumer.poll(timeout=1.0)
        if msg:
            process(msg)
            producer.send_json("results", {"processed": True})
            consumer.commit(msg)
finally:
    producer.flush(timeout=10.0)
    consumer.close()
```

## Type-Safe Topics

Use `TypedTopic` for compile-time type checking across producer and consumer.

```python
from typedkafka import KafkaProducer, KafkaConsumer
from typedkafka.topics import json_topic, string_topic

# Define typed topics once, use everywhere
events = json_topic("user-events")     # TypedTopic[Any]
logs = string_topic("application-logs") # TypedTopic[str]

# Producer — IDE catches type mismatches
producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
producer.send_typed(events, {"user_id": 123, "action": "click"})
producer.send_typed(logs, "Application started")
# producer.send_typed(logs, {"wrong": "type"})  # IDE error: dict is not str
producer.flush()

# Consumer — decode with type information
consumer = KafkaConsumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-group",
})
consumer.subscribe(["user-events", "application-logs"])

for msg in consumer:
    if msg.topic == "user-events":
        data = msg.decode(events)  # typed as Any
        print(data["user_id"])
    elif msg.topic == "application-logs":
        text = msg.decode(logs)    # typed as str
        print(text.upper())
```

## Structured Logging

Add structured logging to Kafka operations.

```python
import logging
from typedkafka import KafkaProducer, KafkaConsumer
from typedkafka.logging import KafkaLogger, LogContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

kafka_logger = KafkaLogger(
    logging.getLogger("kafka"),
    default_context=LogContext(client_id="my-service"),
)

producer = KafkaProducer(
    {"bootstrap.servers": "localhost:9092"},
    logger=kafka_logger,
)

# Sends, transactions, and errors are logged automatically
producer.send("events", b"message")
# Output: INFO kafka - send topic=events client_id=my-service
```

## Consumer Lag Monitoring

Track consumer metrics and statistics.

```python
from typedkafka import KafkaConsumer
from typedkafka.metrics import KafkaStats

def on_stats(stats: KafkaStats):
    """Called every statistics.interval.ms."""
    for topic, data in stats.raw.get("topics", {}).items():
        for pid, pdata in data.get("partitions", {}).items():
            lag = pdata.get("consumer_lag", -1)
            if lag > 10000:
                print(f"High lag on {topic}[{pid}]: {lag}")

consumer = KafkaConsumer(
    {
        "bootstrap.servers": "localhost:9092",
        "group.id": "my-group",
        "statistics.interval.ms": 5000,
    },
    on_stats=on_stats,
)
consumer.subscribe(["events"])

for msg in consumer:
    process(msg)
    consumer.commit(msg)
    # Check runtime metrics
    print(f"Received: {consumer.metrics.messages_received}")
```

## Dead Letter Queue with Retry

Combine retry logic with a dead letter queue for robust message processing.

```python
from typedkafka import KafkaProducer, KafkaConsumer
from typedkafka.dlq import DeadLetterQueue, process_with_dlq
from typedkafka.retry import retry, RetryPolicy

dlq_producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
dlq = DeadLetterQueue(dlq_producer)

consumer = KafkaConsumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-group",
    "enable.auto.commit": False,
})
consumer.subscribe(["orders"])

policy = RetryPolicy(max_attempts=3, initial_delay=1.0, max_delay=10.0)

@retry(policy)
def handle(msg):
    data = msg.value_as_json()
    save_to_database(data)

for msg in consumer:
    success = process_with_dlq(msg, handle, dlq)
    consumer.commit(msg)

print(f"Sent {dlq.send_count} messages to DLQ")
```

## Tips

- **Transactions add overhead** — batch multiple operations in a single transaction.
- **Use DLQ for poison messages** — don't let one bad message block the pipeline.
- **Monitor consumer lag** — enable `statistics.interval.ms` in production.
- **Type your topics** — `TypedTopic` catches serialization bugs at development time.
- **Log selectively** — `KafkaLogger` is a no-op when `logger=None`, so you can toggle it per environment.
