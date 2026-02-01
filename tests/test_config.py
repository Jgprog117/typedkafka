"""Tests for configuration builders."""

import pytest

from typedkafka.config import ConsumerConfig, ProducerConfig
from typedkafka.exceptions import ConfigurationError


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

    def test_acks_validation_valid(self):
        """Test that valid acks values are accepted."""
        for acks in ("0", "1", "all", 0, 1, -1):
            config = ProducerConfig().acks(acks).build()
            assert config["acks"] == acks

    def test_acks_validation_invalid(self):
        """Test that invalid acks values raise ValueError."""
        with pytest.raises(ValueError, match="Invalid acks"):
            ProducerConfig().acks("invalid")

    def test_compression_validation_valid(self):
        """Test that valid compression types are accepted."""
        for comp in ("none", "gzip", "snappy", "lz4", "zstd"):
            config = ProducerConfig().compression(comp).build()
            assert config["compression.type"] == comp

    def test_compression_validation_invalid(self):
        """Test that invalid compression types raise ValueError."""
        with pytest.raises(ValueError, match="Invalid compression"):
            ProducerConfig().compression("brotli")

    def test_linger_ms_validation(self):
        """Test that negative linger_ms raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            ProducerConfig().linger_ms(-1)

    def test_linger_ms_valid(self):
        """Test that valid linger_ms is accepted."""
        config = ProducerConfig().linger_ms(0).build()
        assert config["linger.ms"] == 0
        config = ProducerConfig().linger_ms(100).build()
        assert config["linger.ms"] == 100

    def test_batch_size_validation(self):
        """Test that negative batch_size raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            ProducerConfig().batch_size(-1)

    def test_batch_size_valid(self):
        """Test that valid batch_size is accepted."""
        config = ProducerConfig().batch_size(32768).build()
        assert config["batch.size"] == 32768

    def test_retries(self):
        """Test setting retries."""
        config = ProducerConfig().retries(5).build()
        assert config["retries"] == 5

    def test_max_in_flight_requests(self):
        """Test setting max in-flight requests."""
        config = ProducerConfig().max_in_flight_requests(1).build()
        assert config["max.in.flight.requests.per.connection"] == 1

    def test_client_id(self):
        """Test setting client ID."""
        config = ProducerConfig().client_id("my-producer").build()
        assert config["client.id"] == "my-producer"

    def test_empty_build(self):
        """Test building empty config."""
        config = ProducerConfig().build()
        assert config == {}

    def test_build_validated_missing_bootstrap(self):
        """Test build(validate=True) raises when bootstrap.servers missing."""
        with pytest.raises(ConfigurationError, match="bootstrap.servers"):
            ProducerConfig().acks("all").build(validate=True)

    def test_build_validated_passes(self):
        """Test build(validate=True) passes with required fields."""
        config = ProducerConfig().bootstrap_servers("localhost:9092").build(validate=True)
        assert config["bootstrap.servers"] == "localhost:9092"

    def test_sasl_plain(self):
        """Test SASL/PLAIN configuration."""
        config = ProducerConfig().sasl_plain("user", "pass").build()
        assert config["security.protocol"] == "SASL_PLAINTEXT"
        assert config["sasl.mechanisms"] == "PLAIN"
        assert config["sasl.username"] == "user"
        assert config["sasl.password"] == "pass"

    def test_sasl_scram(self):
        """Test SASL/SCRAM configuration."""
        config = ProducerConfig().sasl_scram("user", "pass").build()
        assert config["security.protocol"] == "SASL_SSL"
        assert config["sasl.mechanisms"] == "SCRAM-SHA-256"

    def test_sasl_scram_custom_mechanism(self):
        """Test SASL/SCRAM with custom mechanism."""
        config = ProducerConfig().sasl_scram("u", "p", mechanism="SCRAM-SHA-512").build()
        assert config["sasl.mechanisms"] == "SCRAM-SHA-512"

    def test_ssl(self):
        """Test SSL configuration."""
        config = ProducerConfig().ssl("/ca.pem").build()
        assert config["security.protocol"] == "SSL"
        assert config["ssl.ca.location"] == "/ca.pem"
        assert "ssl.certificate.location" not in config

    def test_ssl_with_client_cert(self):
        """Test SSL with client certificate."""
        config = ProducerConfig().ssl("/ca.pem", "/cert.pem", "/key.pem").build()
        assert config["ssl.certificate.location"] == "/cert.pem"
        assert config["ssl.key.location"] == "/key.pem"


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

    def test_auto_offset_reset_validation_invalid(self):
        """Test that invalid auto_offset_reset raises ValueError."""
        with pytest.raises(ValueError, match="Invalid auto_offset_reset"):
            ConsumerConfig().auto_offset_reset("invalid")

    def test_auto_offset_reset_validation_valid(self):
        """Test that all valid offset reset values are accepted."""
        for reset in ("earliest", "latest", "none"):
            config = ConsumerConfig().auto_offset_reset(reset).build()
            assert config["auto.offset.reset"] == reset

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

    def test_auto_commit_interval_ms(self):
        """Test setting auto commit interval."""
        config = ConsumerConfig().auto_commit_interval_ms(1000).build()
        assert config["auto.commit.interval.ms"] == 1000

    def test_max_poll_interval_ms(self):
        """Test setting max poll interval."""
        config = ConsumerConfig().max_poll_interval_ms(600000).build()
        assert config["max.poll.interval.ms"] == 600000

    def test_max_poll_records(self):
        """Test setting max poll records."""
        config = ConsumerConfig().max_poll_records(500).build()
        assert config["max.poll.records"] == 500

    def test_session_timeout_ms(self):
        """Test setting session timeout."""
        config = ConsumerConfig().session_timeout_ms(30000).build()
        assert config["session.timeout.ms"] == 30000

    def test_custom_config(self):
        """Test setting custom configuration."""
        config = ConsumerConfig().set("fetch.min.bytes", 1024).build()
        assert config["fetch.min.bytes"] == 1024

    def test_build_returns_copy(self):
        """Test that build() returns a copy."""
        builder = ConsumerConfig().group_id("test")
        config1 = builder.build()
        config2 = builder.build()
        assert config1 is not config2
        assert config1 == config2

    def test_client_id(self):
        """Test setting client ID."""
        config = ConsumerConfig().client_id("my-consumer").build()
        assert config["client.id"] == "my-consumer"

    def test_empty_build(self):
        """Test building empty config."""
        config = ConsumerConfig().build()
        assert config == {}

    def test_build_validated_missing_bootstrap(self):
        """Test build(validate=True) raises when bootstrap.servers missing."""
        with pytest.raises(ConfigurationError, match="bootstrap.servers"):
            ConsumerConfig().group_id("test").build(validate=True)

    def test_build_validated_missing_group_id(self):
        """Test build(validate=True) raises when group.id missing."""
        with pytest.raises(ConfigurationError, match="group.id"):
            ConsumerConfig().bootstrap_servers("localhost:9092").build(validate=True)

    def test_build_validated_passes(self):
        """Test build(validate=True) passes with required fields."""
        config = (
            ConsumerConfig()
            .bootstrap_servers("localhost:9092")
            .group_id("test")
            .build(validate=True)
        )
        assert config["bootstrap.servers"] == "localhost:9092"
        assert config["group.id"] == "test"

    def test_sasl_plain(self):
        """Test SASL/PLAIN configuration."""
        config = ConsumerConfig().sasl_plain("user", "pass").build()
        assert config["security.protocol"] == "SASL_PLAINTEXT"
        assert config["sasl.mechanisms"] == "PLAIN"

    def test_sasl_scram(self):
        """Test SASL/SCRAM configuration."""
        config = ConsumerConfig().sasl_scram("user", "pass").build()
        assert config["security.protocol"] == "SASL_SSL"
        assert config["sasl.mechanisms"] == "SCRAM-SHA-256"

    def test_ssl(self):
        """Test SSL configuration."""
        config = ConsumerConfig().ssl("/ca.pem", "/cert.pem").build()
        assert config["security.protocol"] == "SSL"
        assert config["ssl.ca.location"] == "/ca.pem"
        assert config["ssl.certificate.location"] == "/cert.pem"

    def test_from_env(self, monkeypatch):
        """Test loading consumer config from environment variables."""
        monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")
        monkeypatch.setenv("KAFKA_GROUP_ID", "my-group")
        monkeypatch.setenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
        config = ConsumerConfig.from_env().build()
        assert config["bootstrap.servers"] == "broker:9092"
        assert config["group.id"] == "my-group"
        assert config["auto.offset.reset"] == "earliest"


class TestProducerConfigPresets:
    """Test ProducerConfig presets and new methods."""

    def test_enable_idempotence(self):
        """Test enable_idempotence method."""
        config = ProducerConfig().enable_idempotence().build()
        assert config["enable.idempotence"] is True

    def test_transactional_id(self):
        """Test transactional_id method."""
        config = ProducerConfig().transactional_id("my-txn").build()
        assert config["transactional.id"] == "my-txn"

    def test_high_throughput_preset(self):
        """Test high_throughput preset."""
        config = ProducerConfig.high_throughput("broker:9092").build()
        assert config["bootstrap.servers"] == "broker:9092"
        assert config["acks"] == "1"
        assert config["compression.type"] == "lz4"
        assert config["linger.ms"] == 50
        assert config["batch.size"] == 65536

    def test_exactly_once_preset(self):
        """Test exactly_once preset."""
        config = ProducerConfig.exactly_once("broker:9092", "txn-1").build()
        assert config["bootstrap.servers"] == "broker:9092"
        assert config["acks"] == "all"
        assert config["enable.idempotence"] is True
        assert config["transactional.id"] == "txn-1"

    def test_exactly_once_validates(self):
        """Test exactly_once preset passes validation."""
        config = ProducerConfig.exactly_once("broker:9092", "txn-1").build(validate=True)
        assert config["transactional.id"] == "txn-1"

    def test_validate_idempotence_requires_acks_all(self):
        """Test validation catches idempotence without acks=all."""
        with pytest.raises(ConfigurationError, match="acks='all'"):
            (
                ProducerConfig()
                .bootstrap_servers("broker:9092")
                .acks("1")
                .enable_idempotence()
                .build(validate=True)
            )

    def test_validate_transactional_requires_idempotence(self):
        """Test validation catches transactional.id without idempotence."""
        with pytest.raises(ConfigurationError, match="enable.idempotence"):
            (
                ProducerConfig()
                .bootstrap_servers("broker:9092")
                .transactional_id("txn-1")
                .build(validate=True)
            )

    def test_from_env(self, monkeypatch):
        """Test loading producer config from environment variables."""
        monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")
        monkeypatch.setenv("KAFKA_ACKS", "all")
        monkeypatch.setenv("KAFKA_COMPRESSION", "gzip")
        monkeypatch.setenv("KAFKA_LINGER_MS", "10")
        config = ProducerConfig.from_env().build()
        assert config["bootstrap.servers"] == "broker:9092"
        assert config["acks"] == "all"
        assert config["compression.type"] == "gzip"
        assert config["linger.ms"] == 10

    def test_from_env_custom_prefix(self, monkeypatch):
        """Test from_env with custom prefix."""
        monkeypatch.setenv("APP_BOOTSTRAP_SERVERS", "broker:9092")
        config = ProducerConfig.from_env(prefix="APP_").build()
        assert config["bootstrap.servers"] == "broker:9092"

    def test_from_env_empty(self):
        """Test from_env returns empty config when no env vars set."""
        config = ProducerConfig.from_env(prefix="NONEXISTENT_").build()
        assert config == {}
