"""Extended tests for KafkaAdmin to increase coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from typedkafka.admin import AdminError, KafkaAdmin


class TestKafkaAdminWithMock:
    """Test KafkaAdmin methods using mocked confluent admin client."""

    @pytest.fixture
    def admin(self):
        """Create a KafkaAdmin with mocked internals."""
        a = KafkaAdmin.__new__(KafkaAdmin)
        a.config = {"bootstrap.servers": "localhost:9092"}
        a._admin = MagicMock()
        return a

    def test_create_topic_success(self, admin):
        future = MagicMock()
        future.result.return_value = None
        admin._admin.create_topics.return_value = {"my-topic": future}
        admin.create_topic("my-topic", num_partitions=3, replication_factor=2)
        admin._admin.create_topics.assert_called_once()

    def test_create_topic_with_config(self, admin):
        future = MagicMock()
        future.result.return_value = None
        admin._admin.create_topics.return_value = {"t": future}
        admin.create_topic("t", config={"retention.ms": "1000"})
        admin._admin.create_topics.assert_called_once()

    def test_create_topic_future_error(self, admin):
        future = MagicMock()
        future.result.side_effect = RuntimeError("topic exists")
        admin._admin.create_topics.return_value = {"my-topic": future}
        with pytest.raises(AdminError, match="Failed to create topic"):
            admin.create_topic("my-topic")

    def test_create_topic_general_error(self, admin):
        admin._admin.create_topics.side_effect = RuntimeError("connection failed")
        with pytest.raises(AdminError, match="Failed to create topic"):
            admin.create_topic("my-topic")

    def test_delete_topic_success(self, admin):
        future = MagicMock()
        future.result.return_value = None
        admin._admin.delete_topics.return_value = {"my-topic": future}
        admin.delete_topic("my-topic")
        admin._admin.delete_topics.assert_called_once()

    def test_delete_topic_future_error(self, admin):
        future = MagicMock()
        future.result.side_effect = RuntimeError("not found")
        admin._admin.delete_topics.return_value = {"my-topic": future}
        with pytest.raises(AdminError, match="Failed to delete topic"):
            admin.delete_topic("my-topic")

    def test_delete_topic_general_error(self, admin):
        admin._admin.delete_topics.side_effect = RuntimeError("connection failed")
        with pytest.raises(AdminError, match="Failed to delete topic"):
            admin.delete_topic("my-topic")

    def test_list_topics(self, admin):
        metadata = MagicMock()
        metadata.topics = {"topic1": MagicMock(), "topic2": MagicMock()}
        admin._admin.list_topics.return_value = metadata
        result = admin.list_topics()
        assert set(result) == {"topic1", "topic2"}

    def test_list_topics_error(self, admin):
        admin._admin.list_topics.side_effect = RuntimeError("fail")
        with pytest.raises(AdminError, match="Failed to list topics"):
            admin.list_topics()

    def test_topic_exists_true(self, admin):
        metadata = MagicMock()
        metadata.topics = {"my-topic": MagicMock()}
        admin._admin.list_topics.return_value = metadata
        assert admin.topic_exists("my-topic") is True

    def test_topic_exists_false(self, admin):
        metadata = MagicMock()
        metadata.topics = {"other": MagicMock()}
        admin._admin.list_topics.return_value = metadata
        assert admin.topic_exists("my-topic") is False

    def test_topic_exists_error(self, admin):
        admin._admin.list_topics.side_effect = RuntimeError("fail")
        with pytest.raises(AdminError, match="Failed to check if topic exists"):
            admin.topic_exists("my-topic")

    def test_describe_topic(self, admin):
        partition = MagicMock()
        partition.id = 0
        partition.leader = 1
        partition.replicas = [1, 2]
        partition.isrs = [1, 2]
        topic_meta = MagicMock()
        topic_meta.partitions = {0: partition}
        metadata = MagicMock()
        metadata.topics = {"my-topic": topic_meta}
        admin._admin.list_topics.return_value = metadata
        result = admin.describe_topic("my-topic")
        assert result["topic"] == "my-topic"
        assert len(result["partitions"]) == 1
        assert result["partitions"][0]["id"] == 0
        assert result["partitions"][0]["leader"] == 1

    def test_describe_topic_not_found(self, admin):
        metadata = MagicMock()
        topics_dict = MagicMock()
        topics_dict.get.return_value = None
        metadata.topics = topics_dict
        admin._admin.list_topics.return_value = metadata
        with pytest.raises(AdminError, match="not found"):
            admin.describe_topic("missing-topic")

    def test_describe_topic_general_error(self, admin):
        admin._admin.list_topics.side_effect = RuntimeError("fail")
        with pytest.raises(AdminError, match="Failed to describe topic"):
            admin.describe_topic("my-topic")


class TestKafkaAdminInitErrors:
    """Test KafkaAdmin init edge cases."""

    def test_init_without_confluent_kafka(self):
        with patch("typedkafka.admin.ConfluentAdminClient", None):
            with pytest.raises(ImportError, match="confluent-kafka"):
                KafkaAdmin({})

    def test_init_error_wraps_exception(self):
        with patch(
            "typedkafka.admin.ConfluentAdminClient", side_effect=RuntimeError("bad config")
        ):
            with pytest.raises(AdminError, match="Failed to initialize"):
                KafkaAdmin({"bootstrap.servers": "bad"})
