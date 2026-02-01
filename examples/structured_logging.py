"""Structured logging for Kafka operations.

KafkaLogger wraps Python's stdlib logging with Kafka-specific context.
Pass it to KafkaProducer or KafkaConsumer to automatically log sends,
polls, commits, transactions, and errors.
"""

import logging

from typedkafka import KafkaConsumer, KafkaProducer
from typedkafka.logging import KafkaLogger, LogContext

# Configure Python stdlib logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

# Create loggers with default context
producer_logger = KafkaLogger(
    logging.getLogger("kafka.producer"),
    default_context=LogContext(client_id="my-service"),
)

consumer_logger = KafkaLogger(
    logging.getLogger("kafka.consumer"),
    default_context=LogContext(group_id="my-group", client_id="my-service"),
)

# Use with producer — sends are logged automatically
producer = KafkaProducer(
    {"bootstrap.servers": "localhost:9092"},
    logger=producer_logger,
)
producer.send("events", b"message")
# Output: INFO kafka.producer - send topic=events client_id=my-service

producer.flush()

# Use with consumer — polls and commits are logged
consumer = KafkaConsumer(
    {
        "bootstrap.servers": "localhost:9092",
        "group.id": "my-group",
        "auto.offset.reset": "earliest",
    },
    logger=consumer_logger,
)
consumer.subscribe(["events"])

msg = consumer.poll(timeout=5.0)
if msg:
    consumer.commit(msg)
    # Output: INFO kafka.consumer - commit topic=events partition=0 offset=0 group_id=my-group client_id=my-service
