"""Dead Letter Queue (DLQ) for handling failed messages."""

from typedkafka import DeadLetterQueue, KafkaConsumer, KafkaProducer, process_with_dlq

# --- Basic DLQ setup ---

producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
dlq = DeadLetterQueue(producer)
# Failed messages from "orders" go to "orders.dlq" by default

consumer = KafkaConsumer(
    {
        "bootstrap.servers": "localhost:9092",
        "group.id": "order-processor",
        "auto.offset.reset": "earliest",
    }
)
consumer.subscribe(["orders"])


def process_order(msg):
    data = msg.value_as_json()
    if "order_id" not in data:
        raise ValueError("Missing order_id")
    print(f"Processed order {data['order_id']}")


# --- Manual DLQ routing ---

for msg in consumer:
    try:
        process_order(msg)
        consumer.commit(msg)
    except Exception as e:
        dlq.send(msg, error=e)
        consumer.commit(msg)  # commit so we don't reprocess
        print(f"Sent to DLQ: {e}")

# --- Using process_with_dlq helper ---

for msg in consumer:
    success = process_with_dlq(msg, process_order, dlq)
    if success:
        consumer.commit(msg)
    else:
        consumer.commit(msg)  # still commit to move past the bad message

# --- Custom DLQ topic naming ---

dlq_custom = DeadLetterQueue(producer, topic_fn=lambda t: f"errors.{t}")
# "orders" failures go to "errors.orders"

# --- Fixed DLQ topic ---

dlq_fixed = DeadLetterQueue(producer, default_topic="all-errors")
# All failures go to "all-errors" regardless of source topic

# --- Extra headers ---

for msg in consumer:
    try:
        process_order(msg)
    except Exception as e:
        dlq.send(
            msg,
            error=e,
            extra_headers=[("retry-count", b"3"), ("service", b"order-processor")],
        )

# --- Tracking DLQ volume ---

print(f"Messages sent to DLQ: {dlq.send_count}")

consumer.close()
producer.close()
