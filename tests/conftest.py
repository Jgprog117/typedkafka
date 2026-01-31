"""Shared test fixtures for typedkafka tests."""

import pytest

from typedkafka.testing import MockConsumer, MockProducer


@pytest.fixture
def mock_producer():
    """Create a MockProducer instance."""
    return MockProducer()


@pytest.fixture
def mock_consumer():
    """Create a MockConsumer instance."""
    return MockConsumer()


@pytest.fixture
def producer_config():
    """Return a minimal producer configuration dict."""
    return {"bootstrap.servers": "localhost:9092"}


@pytest.fixture
def consumer_config():
    """Return a minimal consumer configuration dict."""
    return {
        "bootstrap.servers": "localhost:9092",
        "group.id": "test-group",
        "auto.offset.reset": "earliest",
    }
