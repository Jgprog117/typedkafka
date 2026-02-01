"""Integration tests for KafkaAdmin operations."""

from __future__ import annotations

from tests.integration.conftest import integration


@integration
class TestAdminIntegration:
    """Test admin topic management against a real broker."""

    def test_create_and_list_topics(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=2, replication_factor=1)

        try:
            topics = admin.list_topics()
            assert unique_topic in topics
        finally:
            admin.delete_topic(unique_topic)

    def test_topic_exists(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin

        admin = KafkaAdmin(producer_config)
        assert not admin.topic_exists(unique_topic)

        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        try:
            assert admin.topic_exists(unique_topic)
        finally:
            admin.delete_topic(unique_topic)

    def test_describe_topic(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=3, replication_factor=1)

        try:
            info = admin.describe_topic(unique_topic)
            assert isinstance(info, dict)
            assert info["topic"] == unique_topic
            assert len(info["partitions"]) == 3
        finally:
            admin.delete_topic(unique_topic)

    def test_create_topic_with_config(self, producer_config, unique_topic):
        from typedkafka import KafkaAdmin

        admin = KafkaAdmin(producer_config)
        admin.create_topic(
            unique_topic,
            num_partitions=1,
            replication_factor=1,
            config={"retention.ms": "3600000"},
        )

        try:
            assert admin.topic_exists(unique_topic)
        finally:
            admin.delete_topic(unique_topic)
