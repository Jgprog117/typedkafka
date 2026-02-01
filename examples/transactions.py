"""Transaction support with context manager and error handling."""

from typedkafka import KafkaProducer
from typedkafka.exceptions import TransactionError

producer = KafkaProducer({
    "bootstrap.servers": "localhost:9092",
    "transactional.id": "my-txn-id",
})
producer.init_transactions()

# Commits on success, aborts on exception
with producer.transaction():
    producer.send("topic", b"msg1")
    producer.send("topic", b"msg2")

# v0.6.0: TransactionError for transaction-specific failures
try:
    with producer.transaction():
        producer.send("topic", b"msg3")
        raise ValueError("business logic error")  # triggers abort
except ValueError:
    print("Transaction was aborted due to business error")

# Transaction methods raise TransactionError (not ProducerError)
try:
    producer.init_transactions()
except TransactionError as e:
    print(f"Transaction init failed: {e}")
    if e.context:
        print(f"  Error context: {e.context}")
