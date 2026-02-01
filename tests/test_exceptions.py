"""Tests for exception classes."""

import pytest

from typedkafka.exceptions import (
    ConfigurationError,
    ConsumerError,
    KafkaError,
    KafkaErrorContext,
    ProducerError,
    SerializationError,
    TransactionError,
)


class TestExceptions:
    """Test exception hierarchy and attributes."""

    def test_kafka_error_is_base(self):
        """Test that all exceptions inherit from KafkaError."""
        assert issubclass(ProducerError, KafkaError)
        assert issubclass(ConsumerError, KafkaError)
        assert issubclass(SerializationError, KafkaError)
        assert issubclass(ConfigurationError, KafkaError)
        assert issubclass(TransactionError, KafkaError)

    def test_producer_error_attributes(self):
        """Test ProducerError stores original error."""
        original = ValueError("test error")
        error = ProducerError("Failed to produce", original_error=original)
        assert error.original_error is original
        assert "Failed to produce" in str(error)

    def test_consumer_error_attributes(self):
        """Test ConsumerError stores original error."""
        original = ConnectionError("broker down")
        error = ConsumerError("Failed to consume", original_error=original)
        assert error.original_error is original

    def test_serialization_error_attributes(self):
        """Test SerializationError stores value and original error."""
        value = {"invalid": object()}
        original = TypeError("not serializable")
        error = SerializationError(
            "Serialization failed",
            value=value,
            original_error=original
        )
        assert error.value == value
        assert error.original_error is original

    def test_can_catch_all_kafka_errors(self):
        """Test that all Kafka exceptions can be caught with KafkaError."""
        errors = [
            ProducerError("producer error"),
            ConsumerError("consumer error"),
            SerializationError("serialization error"),
            ConfigurationError("config error"),
            TransactionError("transaction error"),
        ]

        for error in errors:
            with pytest.raises(KafkaError):
                raise error

    def test_error_context(self):
        """Test KafkaErrorContext is attached to errors."""
        ctx = KafkaErrorContext(topic="my-topic", partition=0, offset=42)
        error = ProducerError("fail", context=ctx)
        assert error.context.topic == "my-topic"
        assert error.context.partition == 0
        assert error.context.offset == 42

    def test_error_context_in_str(self):
        """Test that context fields appear in string representation."""
        ctx = KafkaErrorContext(topic="events", partition=3)
        original = RuntimeError("boom")
        error = ConsumerError("poll failed", context=ctx, original_error=original)
        s = str(error)
        assert "topic=events" in s
        assert "partition=3" in s
        assert "caused_by=RuntimeError: boom" in s

    def test_default_context(self):
        """Test that errors get an empty context by default."""
        error = KafkaError("test")
        assert error.context is not None
        assert error.context.topic is None

    def test_transaction_error_is_kafka_error(self):
        """Test TransactionError can be caught as KafkaError."""
        with pytest.raises(KafkaError):
            raise TransactionError("txn failed")

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("bootstrap.servers is required")
        assert "bootstrap.servers" in str(error)
