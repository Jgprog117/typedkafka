"""Integration tests for TypedTopic with a real broker."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestTypedTopicIntegration:
    """Test TypedTopic end-to-end with a real broker."""

    def test_json_topic_roundtrip(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.topics import json_topic

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        events = json_topic(unique_topic)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_typed(events, {"user_id": 123, "action": "click"})
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                data = msg.decode(events)
                assert data == {"user_id": 123, "action": "click"}
        finally:
            admin.delete_topic(unique_topic)

    def test_string_topic_roundtrip(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.topics import string_topic

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        logs = string_topic(unique_topic)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_typed(logs, "Application started")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                text = msg.decode(logs)
                assert text == "Application started"
        finally:
            admin.delete_topic(unique_topic)

    def test_typed_topic_with_key_serializer(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.serializers import (
            JsonDeserializer,
            JsonSerializer,
            StringSerializer,
        )
        from typedkafka.topics import TypedTopic

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        topic = TypedTopic(
            unique_topic,
            value_serializer=JsonSerializer(),
            value_deserializer=JsonDeserializer(),
            key_serializer=StringSerializer(),
        )

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_typed(topic, {"order": 1}, key="order-123")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.decode(topic) == {"order": 1}
                assert msg.key_as_string() == "order-123"
        finally:
            admin.delete_topic(unique_topic)

    def test_typed_topic_with_headers(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.topics import json_topic

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        events = json_topic(unique_topic)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_typed(
                    events,
                    {"id": 1},
                    headers=[("trace-id", b"abc123")],
                )
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                assert msg.decode(events) == {"id": 1}
                headers = dict(msg.headers)
                assert headers["trace-id"] == b"abc123"
        finally:
            admin.delete_topic(unique_topic)

    def test_multiple_typed_topics(self, producer_config, consumer_config, unique_topic):
        """Send to two typed topics and consume from both."""
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.topics import json_topic, string_topic

        admin = KafkaAdmin(producer_config)
        json_name = f"{unique_topic}-json"
        str_name = f"{unique_topic}-str"
        admin.create_topic(json_name, num_partitions=1, replication_factor=1)
        admin.create_topic(str_name, num_partitions=1, replication_factor=1)

        events = json_topic(json_name)
        logs = string_topic(str_name)

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_typed(events, {"id": 1})
                producer.send_typed(logs, "hello")
                producer.flush()

            with KafkaConsumer(consumer_config) as consumer:
                consumer.subscribe([json_name, str_name])
                received = {}
                for _ in range(20):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        received[msg.topic] = msg
                    if len(received) >= 2:
                        break

                assert json_name in received
                assert str_name in received
                assert received[json_name].decode(events) == {"id": 1}
                assert received[str_name].decode(logs) == "hello"
        finally:
            admin.delete_topic(json_name)
            admin.delete_topic(str_name)
