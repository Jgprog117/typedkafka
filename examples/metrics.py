"""Metrics and statistics collection."""

from typedkafka import KafkaConsumer, KafkaProducer, KafkaStats, ProducerConfig

# --- Producer with metrics ---

# Enable stats reporting every 5 seconds via config
producer = KafkaProducer(
    {"bootstrap.servers": "localhost:9092", "statistics.interval.ms": 5000}
)

producer.send("events", b"hello")
producer.send("events", b"world")

# Access simple counters (always available)
print(f"Messages sent: {producer.metrics.messages_sent}")
print(f"Errors: {producer.metrics.errors}")

# Byte counters are populated by the stats callback
print(f"Bytes sent: {producer.metrics.bytes_sent}")

# Access the last raw stats snapshot
if producer.metrics.last_stats:
    stats: KafkaStats = producer.metrics.last_stats
    print(f"Client: {stats.name} ({stats.client_type})")
    print(f"TX bytes: {stats.txbytes}, RX bytes: {stats.rxbytes}")
    print(f"Messages in queue: {stats.msg_cnt}")
    # Full raw dict for advanced use
    print(f"Broker count: {len(stats.raw.get('brokers', {}))}")

producer.flush()

# --- Consumer with metrics ---

consumer = KafkaConsumer(
    {
        "bootstrap.servers": "localhost:9092",
        "group.id": "metrics-demo",
        "statistics.interval.ms": 5000,
    }
)
consumer.subscribe(["events"])

# Poll some messages
for _ in range(10):
    msg = consumer.poll(timeout=1.0)
    if msg:
        print(f"Received: {msg.value_as_string()}")

print(f"Messages received: {consumer.metrics.messages_received}")
print(f"Bytes received: {consumer.metrics.bytes_received}")

consumer.close()

# --- Custom stats callback ---


def on_stats(stats: KafkaStats) -> None:
    """Called each time confluent-kafka emits statistics."""
    print(f"[{stats.time_seconds}] TX: {stats.txbytes} bytes, RX: {stats.rxbytes} bytes")


producer_with_cb = KafkaProducer(
    {"bootstrap.servers": "localhost:9092", "statistics.interval.ms": 5000},
    on_stats=on_stats,
)

# --- Config builder approach ---

config = (
    ProducerConfig()
    .bootstrap_servers("localhost:9092")
    .stats_interval_ms(5000)
    .build()
)
producer2 = KafkaProducer(config)

# --- Reset metrics ---

producer.metrics.reset()
assert producer.metrics.messages_sent == 0
