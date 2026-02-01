"""Pluggable serializer framework with custom deserialization."""

from typedkafka.serializers import (
    JsonDeserializer,
    JsonSerializer,
    StringDeserializer,
    StringSerializer,
)

# JSON serializer
json_ser = JsonSerializer()
data = json_ser.serialize("topic", {"user_id": 123})

# JSON deserializer
json_deser = JsonDeserializer()
obj = json_deser.deserialize("topic", data)
assert obj == {"user_id": 123}

# String serializer/deserializer with custom encoding
str_ser = StringSerializer(encoding="utf-8")
str_deser = StringDeserializer(encoding="utf-8")
encoded = str_ser.serialize("topic", "hello")
decoded = str_deser.deserialize("topic", encoded)
assert decoded == "hello"

# v0.6.0: value_as() for on-the-fly deserialization
# msg = consumer.poll()
# obj = msg.value_as(json_deser)  # Deserialize with any Deserializer

# v0.6.0: value_deserializer on KafkaConsumer for automatic deserialization
# consumer = KafkaConsumer(
#     {"bootstrap.servers": "localhost:9092", "group.id": "my-group"},
#     value_deserializer=json_deser,
# )
# consumer.subscribe(["events"])
# for msg in consumer:
#     # msg.value is already deserialized via json_deser
#     print(msg.value)

# Avro with Schema Registry (requires typedkafka[avro])
# from typedkafka.serializers import AvroSerializer, AvroDeserializer
# avro_ser = AvroSerializer("http://localhost:8081", schema_str)
# data = avro_ser.serialize("users", {"id": 123, "name": "Alice"})
# avro_deser = AvroDeserializer("http://localhost:8081")
# obj = avro_deser.deserialize("users", data)
