# Getting Started

## Producing Messages

```python
from typedkafka import KafkaProducer

with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    producer.send("my-topic", b"Hello, Kafka!")
    producer.send_json("events", {"user_id": 123, "action": "click"})
    producer.send_string("logs", "Application started")
    producer.flush()
```

## Consuming Messages

```python
from typedkafka import KafkaConsumer

config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-consumer-group",
    "auto.offset.reset": "earliest",
}

with KafkaConsumer(config) as consumer:
    consumer.subscribe(["my-topic"])
    for msg in consumer:
        data = msg.value_as_json()
        print(f"Received: {data}")
        consumer.commit(msg)
```

## Transactions

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

## Async

```python
from typedkafka.aio import AsyncKafkaProducer, AsyncKafkaConsumer

async with AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    await producer.send("topic", b"async message")
    await producer.send_json("events", {"id": 1})
    await producer.flush()
```

## Retry

```python
from typedkafka.retry import retry, RetryPolicy

@retry(max_attempts=3, backoff_base=1.0)
def send_with_retry(producer, data):
    producer.send_json("events", data)
    producer.flush()
```

## Serializers

```python
from typedkafka.serializers import JsonSerializer

json_ser = JsonSerializer()
data = json_ser.serialize("topic", {"user_id": 123})
```

## Type-Safe Configuration

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

## Testing

```python
from typedkafka.testing import MockProducer, MockConsumer

def test_my_producer():
    producer = MockProducer()
    producer.send_json("events", {"user_id": 123})
    producer.flush()
    assert len(producer.messages["events"]) == 1
```
