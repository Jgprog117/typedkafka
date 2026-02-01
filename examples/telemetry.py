"""OpenTelemetry tracing for Kafka operations.

KafkaTracer provides produce_span() and consume_span() context managers
that follow OpenTelemetry semantic conventions. When opentelemetry is not
installed, all operations are graceful no-ops.

Install with: pip install opentelemetry-api opentelemetry-sdk
"""

from typedkafka import KafkaConsumer, KafkaProducer
from typedkafka.telemetry import KafkaTracer

# Create a tracer (no-op if opentelemetry is not installed)
tracer = KafkaTracer(service_name="my-service")

# Produce with tracing
with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
    with tracer.produce_span("events", key="user-123"):
        producer.send_json("events", {"user_id": 123, "action": "click"})

# Consume with tracing
config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-group",
    "auto.offset.reset": "earliest",
}
with KafkaConsumer(config) as consumer:
    consumer.subscribe(["events"])
    msg = consumer.poll(timeout=5.0)
    if msg:
        with tracer.consume_span(msg):
            data = msg.value_as_json()
            print(f"Processing: {data}")
