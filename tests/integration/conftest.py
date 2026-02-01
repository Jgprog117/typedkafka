"""Integration test fixtures and markers.

Set KAFKA_BOOTSTRAP_SERVERS environment variable to run integration tests.
"""

import os
import uuid

import pytest

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
SKIP_INTEGRATION = KAFKA_BOOTSTRAP is None

integration = pytest.mark.skipif(
    SKIP_INTEGRATION,
    reason="Set KAFKA_BOOTSTRAP_SERVERS to run integration tests",
)


@pytest.fixture
def kafka_config():
    """Base Kafka configuration for integration tests."""
    return {
        "bootstrap.servers": KAFKA_BOOTSTRAP,
    }


@pytest.fixture
def unique_topic():
    """Generate a unique topic name for test isolation."""
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def producer_config(kafka_config):
    """Producer configuration."""
    return {**kafka_config}


@pytest.fixture
def consumer_config(kafka_config):
    """Consumer configuration with unique group."""
    return {
        **kafka_config,
        "group.id": f"test-group-{uuid.uuid4().hex[:8]}",
        "auto.offset.reset": "earliest",
    }
