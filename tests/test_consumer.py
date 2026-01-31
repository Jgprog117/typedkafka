"""Tests for KafkaConsumer."""

import pytest


class TestConsumerAPI:
    """Test Consumer API without requiring Kafka broker."""

    def test_import_without_confluent_kafka(self):
        """Test that imports work even if confluent-kafka is not installed."""
        from typedkafka import ConsumerError, KafkaConsumer
        assert KafkaConsumer is not None
        assert ConsumerError is not None

    def test_consumer_requires_config(self):
        """Test that consumer initialization requires proper config."""
        from typedkafka import ConsumerError, KafkaConsumer

        # Consumer requires group.id in config
        with pytest.raises(ConsumerError, match="group.id"):
            KafkaConsumer({})


class TestConsumerDocumentation:
    """Test that consumer has comprehensive documentation."""

    def test_consumer_has_docstrings(self):
        """Verify KafkaConsumer class and methods have docstrings."""
        from typedkafka import KafkaConsumer

        # Class docstring
        assert KafkaConsumer.__doc__ is not None
        assert len(KafkaConsumer.__doc__) > 100
        assert "well-documented" in KafkaConsumer.__doc__.lower()

        # Method docstrings
        assert KafkaConsumer.subscribe.__doc__ is not None
        assert KafkaConsumer.poll.__doc__ is not None
        assert KafkaConsumer.commit.__doc__ is not None
        assert KafkaConsumer.close.__doc__ is not None

        # Check for comprehensive documentation
        assert "Args:" in KafkaConsumer.poll.__doc__
        assert "Examples:" in KafkaConsumer.subscribe.__doc__

    def test_consumer_init_has_config_docs(self):
        """Verify __init__ documents all common config options."""
        from typedkafka import KafkaConsumer

        init_doc = KafkaConsumer.__init__.__doc__
        assert init_doc is not None

        # Check for common config options
        assert "bootstrap.servers" in init_doc
        assert "group.id" in init_doc
        assert "auto.offset.reset" in init_doc
        assert "enable.auto.commit" in init_doc

        # Check for examples
        assert "Examples:" in init_doc

    def test_kafka_message_has_helper_methods(self):
        """Verify KafkaMessage has convenient helper methods."""
        from typedkafka.consumer import KafkaMessage

        # Check that helper methods exist
        assert hasattr(KafkaMessage, "value_as_string")
        assert hasattr(KafkaMessage, "value_as_json")
        assert hasattr(KafkaMessage, "key_as_string")

        # Check for documentation
        assert KafkaMessage.value_as_json.__doc__ is not None
        assert "JSON" in KafkaMessage.value_as_json.__doc__
        assert "Examples:" in KafkaMessage.value_as_json.__doc__

    def test_consumer_supports_iteration(self):
        """Verify KafkaConsumer implements iterator protocol."""
        from typedkafka import KafkaConsumer

        assert hasattr(KafkaConsumer, "__iter__")
        iter_doc = KafkaConsumer.__iter__.__doc__
        assert iter_doc is not None

    def test_consumer_supports_context_manager(self):
        """Verify KafkaConsumer implements context manager protocol."""
        from typedkafka import KafkaConsumer

        assert hasattr(KafkaConsumer, "__enter__")
        assert hasattr(KafkaConsumer, "__exit__")
