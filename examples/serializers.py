"""Pluggable serializer framework."""

from typedkafka.serializers import JsonSerializer

# JSON serializer
json_ser = JsonSerializer()
data = json_ser.serialize("topic", {"user_id": 123})

# Avro with Schema Registry (requires typedkafka[avro])
# from typedkafka.serializers import AvroSerializer
# avro_ser = AvroSerializer("http://localhost:8081", schema_str)
# data = avro_ser.serialize("users", {"id": 123, "name": "Alice"})
