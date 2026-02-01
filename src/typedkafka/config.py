"""
Type-safe configuration builders for Kafka producer and consumer.

Provides fluent API for building Kafka configurations with IDE autocomplete
and validation, preventing common configuration errors.
"""

from typing import Any, Literal, Optional, Union

_VALID_ACKS = {"0", "1", "all", 0, 1, -1}
_VALID_COMPRESSIONS = {"none", "gzip", "snappy", "lz4", "zstd"}
_VALID_OFFSET_RESETS = {"earliest", "latest", "none"}


class _SecurityConfigMixin:
    """Mixin providing security configuration helpers for Kafka config builders."""

    _config: dict[str, Any]

    def sasl_plain(self, username: str, password: str) -> "_SecurityConfigMixin":
        """
        Configure SASL/PLAIN authentication.

        Sets security.protocol to SASL_PLAINTEXT and configures credentials.

        Args:
            username: SASL username
            password: SASL password

        Returns:
            Self for method chaining

        Examples:
            >>> config = ProducerConfig().bootstrap_servers("broker:9092").sasl_plain("user", "pass").build()
        """
        self._config["security.protocol"] = "SASL_PLAINTEXT"
        self._config["sasl.mechanisms"] = "PLAIN"
        self._config["sasl.username"] = username
        self._config["sasl.password"] = password
        return self

    def sasl_scram(
        self,
        username: str,
        password: str,
        mechanism: str = "SCRAM-SHA-256",
    ) -> "_SecurityConfigMixin":
        """
        Configure SASL/SCRAM authentication over SSL.

        Args:
            username: SASL username
            password: SASL password
            mechanism: SCRAM mechanism (default: "SCRAM-SHA-256")

        Returns:
            Self for method chaining

        Examples:
            >>> config = ProducerConfig().bootstrap_servers("broker:9093").sasl_scram("user", "pass").build()
        """
        self._config["security.protocol"] = "SASL_SSL"
        self._config["sasl.mechanisms"] = mechanism
        self._config["sasl.username"] = username
        self._config["sasl.password"] = password
        return self

    def ssl(
        self,
        ca_location: str,
        cert_location: Optional[str] = None,
        key_location: Optional[str] = None,
    ) -> "_SecurityConfigMixin":
        """
        Configure SSL/TLS encryption.

        Args:
            ca_location: Path to CA certificate file
            cert_location: Optional path to client certificate file
            key_location: Optional path to client key file

        Returns:
            Self for method chaining

        Examples:
            >>> config = (ProducerConfig()
            ...     .bootstrap_servers("broker:9093")
            ...     .ssl("/path/to/ca.pem", "/path/to/cert.pem", "/path/to/key.pem")
            ...     .build())
        """
        self._config["security.protocol"] = "SSL"
        self._config["ssl.ca.location"] = ca_location
        if cert_location:
            self._config["ssl.certificate.location"] = cert_location
        if key_location:
            self._config["ssl.key.location"] = key_location
        return self


class ProducerConfig(_SecurityConfigMixin):
    """
    Type-safe builder for Kafka producer configuration.

    Provides a fluent API with full type hints and validation for common
    producer configuration options.

    Examples:
        >>> config = (ProducerConfig()
        ...     .bootstrap_servers("localhost:9092")
        ...     .compression("gzip")
        ...     .acks("all")
        ...     .build())
        >>>
        >>> from typedkafka import KafkaProducer
        >>> producer = KafkaProducer(config)

        >>> # With multiple brokers
        >>> config = (ProducerConfig()
        ...     .bootstrap_servers("broker1:9092,broker2:9092,broker3:9092")
        ...     .client_id("my-application")
        ...     .build())
    """

    def __init__(self) -> None:
        """Initialize an empty producer configuration."""
        self._config: dict[str, Any] = {}

    def bootstrap_servers(self, servers: str) -> "ProducerConfig":
        """
        Set the Kafka broker addresses.

        Args:
            servers: Comma-separated list of broker addresses.
                Example: "localhost:9092" or "broker1:9092,broker2:9092"

        Returns:
            Self for method chaining

        Examples:
            >>> config = ProducerConfig().bootstrap_servers("localhost:9092")
            >>> config = ProducerConfig().bootstrap_servers("b1:9092,b2:9092,b3:9092")
        """
        self._config["bootstrap.servers"] = servers
        return self

    def client_id(self, client_id: str) -> "ProducerConfig":
        """
        Set the client ID for this producer.

        Args:
            client_id: Client identifier string

        Returns:
            Self for method chaining
        """
        self._config["client.id"] = client_id
        return self

    def acks(self, acks: Union[Literal["0", "1", "all"], int]) -> "ProducerConfig":
        """
        Set the number of acknowledgments required.

        Args:
            acks: Acknowledgment level:
                - "0" or 0: No acknowledgment (fire and forget)
                - "1" or 1: Leader acknowledgment only
                - "all" or -1: All in-sync replicas must acknowledge

        Returns:
            Self for method chaining

        Examples:
            >>> config = ProducerConfig().acks("all")  # Maximum durability
            >>> config = ProducerConfig().acks("1")     # Leader only
            >>> config = ProducerConfig().acks("0")     # No acknowledgment
        """
        if acks not in _VALID_ACKS:
            raise ValueError(
                f"Invalid acks value: {acks!r}. Must be one of: '0', '1', 'all', 0, 1, -1"
            )
        self._config["acks"] = acks
        return self

    def compression(
        self, compression_type: Literal["none", "gzip", "snappy", "lz4", "zstd"]
    ) -> "ProducerConfig":
        """
        Set the compression codec.

        Args:
            compression_type: Compression algorithm to use

        Returns:
            Self for method chaining

        Examples:
            >>> config = ProducerConfig().compression("gzip")
            >>> config = ProducerConfig().compression("zstd")  # Best compression
        """
        if compression_type not in _VALID_COMPRESSIONS:
            raise ValueError(
                f"Invalid compression type: {compression_type!r}. "
                f"Must be one of: {', '.join(sorted(_VALID_COMPRESSIONS))}"
            )
        self._config["compression.type"] = compression_type
        return self

    def max_in_flight_requests(self, count: int) -> "ProducerConfig":
        """
        Set maximum number of unacknowledged requests.

        Args:
            count: Max in-flight requests per connection (1-5 recommended)

        Returns:
            Self for method chaining
        """
        self._config["max.in.flight.requests.per.connection"] = count
        return self

    def linger_ms(self, milliseconds: int) -> "ProducerConfig":
        """
        Set time to wait before sending a batch.

        Args:
            milliseconds: Time to wait for more messages before sending

        Returns:
            Self for method chaining

        Examples:
            >>> # Wait up to 10ms to batch messages
            >>> config = ProducerConfig().linger_ms(10)
        """
        if milliseconds < 0:
            raise ValueError(f"linger_ms must be non-negative, got {milliseconds}")
        self._config["linger.ms"] = milliseconds
        return self

    def batch_size(self, bytes_size: int) -> "ProducerConfig":
        """
        Set maximum batch size in bytes.

        Args:
            bytes_size: Maximum batch size (default: 16384)

        Returns:
            Self for method chaining

        Examples:
            >>> config = ProducerConfig().batch_size(32768)  # 32KB batches
        """
        if bytes_size < 0:
            raise ValueError(f"batch_size must be non-negative, got {bytes_size}")
        self._config["batch.size"] = bytes_size
        return self

    def retries(self, count: int) -> "ProducerConfig":
        """
        Set number of retries for failed sends.

        Args:
            count: Number of retries (default: 2147483647 for infinite)

        Returns:
            Self for method chaining
        """
        self._config["retries"] = count
        return self

    def stats_interval_ms(self, milliseconds: int) -> "ProducerConfig":
        """
        Enable statistics reporting at the given interval.

        When set, confluent-kafka will emit internal statistics at this interval.
        Use the ``on_stats`` parameter on ``KafkaProducer`` to receive parsed stats.

        Args:
            milliseconds: Stats reporting interval in milliseconds (e.g. 5000 for every 5s).

        Returns:
            Self for method chaining

        Raises:
            ValueError: If milliseconds is negative.

        Examples:
            >>> config = ProducerConfig().stats_interval_ms(5000).build()
        """
        if milliseconds < 0:
            raise ValueError(f"stats_interval_ms must be non-negative, got {milliseconds}")
        self._config["statistics.interval.ms"] = milliseconds
        return self

    def set(self, key: str, value: Any) -> "ProducerConfig":
        """
        Set a custom configuration parameter.

        Use this for advanced configurations not covered by type-safe methods.

        Args:
            key: Configuration key
            value: Configuration value

        Returns:
            Self for method chaining

        Examples:
            >>> config = ProducerConfig().set("queue.buffering.max.messages", 100000)
        """
        self._config[key] = value
        return self

    def build(self, validate: bool = False) -> dict[str, Any]:
        """
        Build and return the configuration dictionary.

        Args:
            validate: If True, verify that required fields (bootstrap.servers) are set.

        Returns:
            Configuration dict ready for KafkaProducer

        Raises:
            ValueError: If validate is True and required fields are missing.

        Examples:
            >>> config = (ProducerConfig()
            ...     .bootstrap_servers("localhost:9092")
            ...     .acks("all")
            ...     .build())
            >>> from typedkafka import KafkaProducer
            >>> producer = KafkaProducer(config)
        """
        if validate:
            if "bootstrap.servers" not in self._config:
                raise ValueError("bootstrap.servers is required")
        return self._config.copy()


class ConsumerConfig(_SecurityConfigMixin):
    """
    Type-safe builder for Kafka consumer configuration.

    Provides a fluent API with full type hints and validation for common
    consumer configuration options.

    Examples:
        >>> config = (ConsumerConfig()
        ...     .bootstrap_servers("localhost:9092")
        ...     .group_id("my-consumer-group")
        ...     .auto_offset_reset("earliest")
        ...     .build())
        >>>
        >>> from typedkafka import KafkaConsumer
        >>> consumer = KafkaConsumer(config)
    """

    def __init__(self) -> None:
        """Initialize an empty consumer configuration."""
        self._config: dict[str, Any] = {}

    def bootstrap_servers(self, servers: str) -> "ConsumerConfig":
        """
        Set the Kafka broker addresses.

        Args:
            servers: Comma-separated list of broker addresses

        Returns:
            Self for method chaining
        """
        self._config["bootstrap.servers"] = servers
        return self

    def group_id(self, group_id: str) -> "ConsumerConfig":
        """
        Set the consumer group ID (required for subscribe()).

        Args:
            group_id: Consumer group identifier

        Returns:
            Self for method chaining

        Examples:
            >>> config = ConsumerConfig().group_id("my-application-consumers")
        """
        self._config["group.id"] = group_id
        return self

    def client_id(self, client_id: str) -> "ConsumerConfig":
        """
        Set the client ID for this consumer.

        Args:
            client_id: Client identifier string

        Returns:
            Self for method chaining
        """
        self._config["client.id"] = client_id
        return self

    def auto_offset_reset(self, reset: Literal["earliest", "latest", "none"]) -> "ConsumerConfig":
        """
        Set behavior when no initial offset exists.

        Args:
            reset: Offset reset behavior:
                - "earliest": Start from the beginning
                - "latest": Start from the end (skip existing messages)
                - "none": Throw error if no offset exists

        Returns:
            Self for method chaining

        Examples:
            >>> # Process all messages from the beginning
            >>> config = ConsumerConfig().auto_offset_reset("earliest")
            >>>
            >>> # Only process new messages
            >>> config = ConsumerConfig().auto_offset_reset("latest")
        """
        if reset not in _VALID_OFFSET_RESETS:
            raise ValueError(
                f"Invalid auto_offset_reset value: {reset!r}. "
                f"Must be one of: 'earliest', 'latest', 'none'"
            )
        self._config["auto.offset.reset"] = reset
        return self

    def enable_auto_commit(self, enabled: bool = True) -> "ConsumerConfig":
        """
        Enable or disable automatic offset commits.

        Args:
            enabled: True to auto-commit, False for manual commits

        Returns:
            Self for method chaining

        Examples:
            >>> # Manual offset management
            >>> config = ConsumerConfig().enable_auto_commit(False)
        """
        self._config["enable.auto.commit"] = enabled
        return self

    def auto_commit_interval_ms(self, milliseconds: int) -> "ConsumerConfig":
        """
        Set frequency of automatic offset commits.

        Args:
            milliseconds: Commit interval (default: 5000)

        Returns:
            Self for method chaining
        """
        self._config["auto.commit.interval.ms"] = milliseconds
        return self

    def session_timeout_ms(self, milliseconds: int) -> "ConsumerConfig":
        """
        Set consumer session timeout.

        Args:
            milliseconds: Session timeout (default: 10000)

        Returns:
            Self for method chaining
        """
        self._config["session.timeout.ms"] = milliseconds
        return self

    def max_poll_interval_ms(self, milliseconds: int) -> "ConsumerConfig":
        """
        Set maximum time between polls.

        Args:
            milliseconds: Max poll interval (default: 300000)

        Returns:
            Self for method chaining
        """
        self._config["max.poll.interval.ms"] = milliseconds
        return self

    def max_poll_records(self, count: int) -> "ConsumerConfig":
        """
        Set maximum records returned in a single poll.

        Args:
            count: Max records per poll

        Returns:
            Self for method chaining
        """
        self._config["max.poll.records"] = count
        return self

    def stats_interval_ms(self, milliseconds: int) -> "ConsumerConfig":
        """
        Enable statistics reporting at the given interval.

        When set, confluent-kafka will emit internal statistics at this interval.
        Use the ``on_stats`` parameter on ``KafkaConsumer`` to receive parsed stats.

        Args:
            milliseconds: Stats reporting interval in milliseconds (e.g. 5000 for every 5s).

        Returns:
            Self for method chaining

        Raises:
            ValueError: If milliseconds is negative.

        Examples:
            >>> config = ConsumerConfig().stats_interval_ms(5000).build()
        """
        if milliseconds < 0:
            raise ValueError(f"stats_interval_ms must be non-negative, got {milliseconds}")
        self._config["statistics.interval.ms"] = milliseconds
        return self

    def set(self, key: str, value: Any) -> "ConsumerConfig":
        """
        Set a custom configuration parameter.

        Args:
            key: Configuration key
            value: Configuration value

        Returns:
            Self for method chaining
        """
        self._config[key] = value
        return self

    def build(self, validate: bool = False) -> dict[str, Any]:
        """
        Build and return the configuration dictionary.

        Args:
            validate: If True, verify that required fields (bootstrap.servers, group.id)
                are set.

        Returns:
            Configuration dict ready for KafkaConsumer

        Raises:
            ValueError: If validate is True and required fields are missing.
        """
        if validate:
            if "bootstrap.servers" not in self._config:
                raise ValueError("bootstrap.servers is required")
            if "group.id" not in self._config:
                raise ValueError("group.id is required")
        return self._config.copy()
