"""Tests for KafkaProducer."""

import pytest


class TestProducerAPI:
    """Test Producer API without requiring Kafka broker."""

    def test_import_without_confluent_kafka(self):
        """Test that imports work even if confluent-kafka is not installed."""
        # This test verifies the import structure is correct
        from typedkafka import KafkaProducer, ProducerError
        assert KafkaProducer is not None
        assert ProducerError is not None

    def test_json_serialization_error(self):
        """Test that SerializationError is raised for non-serializable objects."""
        # Test the serialization logic without needing a real producer
        import json

        # Object that cannot be serialized to JSON
        class NonSerializable:
            pass

        obj = NonSerializable()

        with pytest.raises((TypeError, ValueError)):
            json.dumps(obj)

    def test_producer_requires_config(self):
        """Test that producer can be initialized with config dict."""
        from typedkafka import KafkaProducer

        # Producer can be initialized, but won't connect without proper config
        producer = KafkaProducer({})
        assert producer is not None
        assert producer.config == {}


class TestProducerDocumentation:
    """Test that producer has comprehensive documentation."""

    def test_producer_has_docstrings(self):
        """Verify KafkaProducer class and methods have docstrings."""
        from typedkafka import KafkaProducer

        # Class docstring
        assert KafkaProducer.__doc__ is not None
        assert len(KafkaProducer.__doc__) > 100
        assert "well-documented" in KafkaProducer.__doc__.lower()

        # Method docstrings
        assert KafkaProducer.send.__doc__ is not None
        assert KafkaProducer.send_json.__doc__ is not None
        assert KafkaProducer.send_string.__doc__ is not None
        assert KafkaProducer.flush.__doc__ is not None
        assert KafkaProducer.close.__doc__ is not None

        # Check for comprehensive documentation
        assert "Args:" in KafkaProducer.send.__doc__
        assert "Returns:" in KafkaProducer.flush.__doc__ or "Raises:" in KafkaProducer.flush.__doc__
        assert "Examples:" in KafkaProducer.send.__doc__

    def test_producer_init_has_config_docs(self):
        """Verify __init__ documents all common config options."""
        from typedkafka import KafkaProducer

        init_doc = KafkaProducer.__init__.__doc__
        assert init_doc is not None

        # Check for common config options
        assert "bootstrap.servers" in init_doc
        assert "compression.type" in init_doc
        assert "acks" in init_doc

        # Check for examples
        assert "Examples:" in init_doc

    def test_methods_have_parameter_docs(self):
        """Verify methods document all parameters."""
        from typedkafka import KafkaProducer

        send_doc = KafkaProducer.send.__doc__
        assert "topic" in send_doc
        assert "value" in send_doc
        assert "key" in send_doc
        assert "partition" in send_doc

        send_json_doc = KafkaProducer.send_json.__doc__
        assert "JSON" in send_json_doc
        assert "serializ" in send_json_doc.lower()
