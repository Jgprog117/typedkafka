"""Tests for configuration builders."""

from typedkafka.config import ConsumerConfig, ProducerConfig


class TestProducerConfig:
    """Test ProducerConfig builder."""

    def test_bootstrap_servers(self):
        """Test setting bootstrap servers."""
        config = ProducerConfig().bootstrap_servers("localhost:9092").build()
        assert config["bootstrap.servers"] == "localhost:9092"

    def test_fluent_api(self):
        """Test fluent API chaining."""
        config = (
            ProducerConfig()
            .bootstrap_servers("broker1:9092,broker2:9092")
            .client_id("my-app")
            .acks("all")
            .compression("gzip")
            .build()
        )

        assert config["bootstrap.servers"] == "broker1:9092,broker2:9092"
        assert config["client.id"] == "my-app"
        assert config["acks"] == "all"
        assert config["compression.type"] == "gzip"

    def test_custom_config(self):
        """Test setting custom configuration."""
        config = ProducerConfig().set("custom.key", "custom.value").build()
        assert config["custom.key"] == "custom.value"

    def test_build_returns_copy(self):
        """Test that build() returns a copy."""
        builder = ProducerConfig().bootstrap_servers("localhost:9092")
        config1 = builder.build()
        config2 = builder.build()

        assert config1 is not config2
        assert config1 == config2


class TestConsumerConfig:
    """Test ConsumerConfig builder."""

    def test_bootstrap_servers_and_group_id(self):
        """Test setting required consumer config."""
        config = (
            ConsumerConfig()
            .bootstrap_servers("localhost:9092")
            .group_id("my-group")
            .build()
        )

        assert config["bootstrap.servers"] == "localhost:9092"
        assert config["group.id"] == "my-group"

    def test_auto_offset_reset(self):
        """Test setting auto offset reset."""
        config = ConsumerConfig().auto_offset_reset("earliest").build()
        assert config["auto.offset.reset"] == "earliest"

    def test_enable_auto_commit(self):
        """Test enabling/disabling auto commit."""
        config1 = ConsumerConfig().enable_auto_commit(True).build()
        config2 = ConsumerConfig().enable_auto_commit(False).build()

        assert config1["enable.auto.commit"] is True
        assert config2["enable.auto.commit"] is False

    def test_fluent_api(self):
        """Test fluent API chaining."""
        config = (
            ConsumerConfig()
            .bootstrap_servers("localhost:9092")
            .group_id("consumers")
            .client_id("consumer-1")
            .auto_offset_reset("latest")
            .enable_auto_commit(False)
            .session_timeout_ms(10000)
            .build()
        )

        assert len(config) == 6
        assert config["bootstrap.servers"] == "localhost:9092"
        assert config["group.id"] == "consumers"
