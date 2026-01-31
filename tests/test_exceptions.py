"""Tests for exception classes."""

import pytest

from typedkafka.exceptions import (
    ConsumerError,
    KafkaError,
    ProducerError,
    SerializationError,
)


class TestExceptions:
    """Test exception hierarchy and attributes."""

    def test_kafka_error_is_base(self):
        """Test that all exceptions inherit from KafkaError."""
        assert issubclass(ProducerError, KafkaError)
        assert issubclass(ConsumerError, KafkaError)
        assert issubclass(SerializationError, KafkaError)

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
        ]

        for error in errors:
            with pytest.raises(KafkaError):
                raise error
