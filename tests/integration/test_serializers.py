"""Integration tests for serializer framework with a real broker."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestSerializerIntegration:
    """Test serializers end-to-end with a real broker."""

    def test_json_serializer_roundtrip(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.serializers import JsonDeserializer, JsonSerializer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        ser = JsonSerializer()
        deser = JsonDeserializer()

        try:
            with KafkaProducer(producer_config) as producer:
                data = {"user_id": 123, "tags": ["a", "b"]}
                producer.send(unique_topic, ser.serialize(unique_topic, data))
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                result = deser.deserialize(unique_topic, msg.value)
                assert result == data
        finally:
            admin.delete_topic(unique_topic)

    def test_string_serializer_roundtrip(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.serializers import StringDeserializer, StringSerializer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        ser = StringSerializer()
        deser = StringDeserializer()

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, ser.serialize(unique_topic, "hello world"))
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                result = deser.deserialize(unique_topic, msg.value)
                assert result == "hello world"
        finally:
            admin.delete_topic(unique_topic)

    def test_string_serializer_latin1(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.serializers import StringDeserializer, StringSerializer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        ser = StringSerializer(encoding="latin-1")
        deser = StringDeserializer(encoding="latin-1")

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send(unique_topic, ser.serialize(unique_topic, "café"))
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert deser.deserialize(unique_topic, msg.value) == "café"
        finally:
            admin.delete_topic(unique_topic)

    def test_value_as_with_deserializer(self, producer_config, consumer_config, unique_topic):
        """Test KafkaMessage.value_as() with a custom deserializer function."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_json(unique_topic, {"count": 42})
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                import json

                result = msg.value_as(lambda b: json.loads(b)["count"])
                assert result == 42
        finally:
            admin.delete_topic(unique_topic)
