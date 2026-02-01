"""Protobuf serialization (requires typedkafka[protobuf]).

Install with: pip install typedkafka[protobuf]
"""

# --- Basic Protobuf serialization ---
# from typedkafka.protobuf import ProtobufSerializer, ProtobufDeserializer
# from my_pb2 import UserEvent  # your generated protobuf class
#
# serializer = ProtobufSerializer()
# deserializer = ProtobufDeserializer(UserEvent)
#
# # Serialize a protobuf message
# event = UserEvent(user_id=123, action="click")
# data = serializer.serialize("events", event)
#
# # Deserialize back
# decoded = deserializer.deserialize("events", data)
# assert decoded.user_id == 123

# --- Helper functions for quick setup ---
# from typedkafka.protobuf import protobuf_serializer_for, protobuf_deserializer_for
#
# serialize_fn = protobuf_serializer_for(UserEvent)
# deserialize_fn = protobuf_deserializer_for(UserEvent)
#
# data = serialize_fn(event)
# decoded = deserialize_fn(data)

# --- Schema Registry Protobuf (requires confluent-kafka[protobuf]) ---
# from typedkafka.protobuf import SchemaRegistryProtobufSerializer
#
# sr_serializer = SchemaRegistryProtobufSerializer("http://localhost:8081")
# data = sr_serializer.serialize("events", event)
#
# # With authentication
# sr_serializer = SchemaRegistryProtobufSerializer(
#     "http://localhost:8081",
#     schema_registry_config={"basic.auth.user.info": "user:pass"},
# )
