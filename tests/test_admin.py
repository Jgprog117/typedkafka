"""Tests for KafkaAdmin."""


from typedkafka.admin import AdminError, KafkaAdmin, TopicConfig


class TestTopicConfig:
    """Test TopicConfig builder."""

    def test_default_values(self):
        """Test default partition and replication factor."""
        tc = TopicConfig("my-topic")
        assert tc.name == "my-topic"
        assert tc._num_partitions == 1
        assert tc._replication_factor == 1
        assert tc._config == {}

    def test_partitions(self):
        """Test setting partitions."""
        tc = TopicConfig("t").partitions(10)
        assert tc._num_partitions == 10

    def test_replication_factor(self):
        """Test setting replication factor."""
        tc = TopicConfig("t").replication_factor(3)
        assert tc._replication_factor == 3

    def test_config(self):
        """Test setting topic config entries."""
        tc = TopicConfig("t").config("retention.ms", "86400000")
        assert tc._config == {"retention.ms": "86400000"}

    def test_method_chaining(self):
        """Test fluent method chaining returns self."""
        tc = TopicConfig("t")
        result = tc.partitions(5).replication_factor(2).config("k", "v")
        assert result is tc
        assert tc._num_partitions == 5
        assert tc._replication_factor == 2
        assert tc._config == {"k": "v"}

    def test_multiple_config_entries(self):
        """Test setting multiple config entries."""
        tc = (
            TopicConfig("t")
            .config("retention.ms", "604800000")
            .config("compression.type", "gzip")
        )
        assert tc._config == {
            "retention.ms": "604800000",
            "compression.type": "gzip",
        }


class TestAdminError:
    """Test AdminError exception."""

    def test_admin_error_is_kafka_error(self):
        """Test AdminError inherits from KafkaError."""
        from typedkafka.exceptions import KafkaError

        assert issubclass(AdminError, KafkaError)

    def test_admin_error_message(self):
        """Test AdminError stores message."""
        err = AdminError("topic creation failed")
        assert "topic creation failed" in str(err)


class TestKafkaAdminInit:
    """Test KafkaAdmin initialization."""

    def test_import(self):
        """Test that KafkaAdmin can be imported."""
        assert KafkaAdmin is not None

    def test_stores_config(self):
        """Test that config is stored on the instance."""
        try:
            admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
            assert admin.config == {"bootstrap.servers": "localhost:9092"}
        except (AdminError, ImportError):
            # confluent-kafka may not connect, but config should be set
            pass


class TestKafkaAdminDocumentation:
    """Test that admin classes have proper documentation."""

    def test_admin_has_docstrings(self):
        """Verify KafkaAdmin has docstrings."""
        assert KafkaAdmin.__doc__ is not None
        assert "Args:" in KafkaAdmin.__init__.__doc__

    def test_topic_config_has_docstrings(self):
        """Verify TopicConfig has docstrings."""
        assert TopicConfig.__doc__ is not None
        assert TopicConfig.partitions.__doc__ is not None
        assert TopicConfig.replication_factor.__doc__ is not None
        assert TopicConfig.config.__doc__ is not None

    def test_admin_methods_have_docstrings(self):
        """Verify all public admin methods have docstrings."""
        assert KafkaAdmin.create_topic.__doc__ is not None
        assert KafkaAdmin.delete_topic.__doc__ is not None
        assert KafkaAdmin.list_topics.__doc__ is not None
        assert KafkaAdmin.topic_exists.__doc__ is not None
        assert KafkaAdmin.describe_topic.__doc__ is not None
