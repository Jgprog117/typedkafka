"""Transaction support with context manager."""

from typedkafka import KafkaProducer

producer = KafkaProducer({
    "bootstrap.servers": "localhost:9092",
    "transactional.id": "my-txn-id",
})
producer.init_transactions()

# Commits on success, aborts on exception
with producer.transaction():
    producer.send("topic", b"msg1")
    producer.send("topic", b"msg2")
