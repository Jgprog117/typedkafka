"""Type-safe topics for compile-time type checking.

TypedTopic binds a topic name to a serializer/deserializer pair,
giving you end-to-end type safety. The existing untyped API (send,
send_json, poll, value_as_json, etc.) is unchanged — TypedTopic is
purely opt-in.
"""

from typedkafka import KafkaConsumer, KafkaProducer
from typedkafka.serializers import JsonDeserializer, JsonSerializer, StringSerializer
from typedkafka.topics import TypedTopic, json_topic, string_topic

# --- Factory functions for common cases ---
events = json_topic("user-events")  # TypedTopic[Any]
logs = string_topic("application-logs")  # TypedTopic[str]

# --- Custom topic with key serializer ---
orders = TypedTopic(
    "orders",
    value_serializer=JsonSerializer(),
    value_deserializer=JsonDeserializer(),
    key_serializer=StringSerializer(),
)

# --- Producer usage ---
producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})

producer.send_typed(events, {"user_id": 123, "action": "click"})
producer.send_typed(logs, "Application started")
producer.send_typed(orders, {"item": "widget", "qty": 5}, key="order-456")

# IDE will flag type mismatches:
# producer.send_typed(logs, {"wrong": "type"})  # Error: dict is not str

producer.flush()

# --- Consumer usage ---
consumer = KafkaConsumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "my-group",
    "auto.offset.reset": "earliest",
})
consumer.subscribe(["user-events", "application-logs"])

for msg in consumer:
    if msg.topic == "user-events":
        event = msg.decode(events)  # typed as Any (JSON)
        print(f"User {event['user_id']} performed {event['action']}")
    elif msg.topic == "application-logs":
        text = msg.decode(logs)  # typed as str
        print(f"LOG: {text.upper()}")
