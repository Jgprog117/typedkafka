"""
Type-safe configuration builders for Kafka producer and consumer.

Provides fluent API for building Kafka configurations with IDE autocomplete
and validation, preventing common configuration errors.
"""

from typing import Any, Literal, Union


class ProducerConfig:
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

    def build(self) -> dict[str, Any]:
        """
        Build and return the configuration dictionary.

        Returns:
            Configuration dict ready for KafkaProducer

        Examples:
            >>> config = (ProducerConfig()
            ...     .bootstrap_servers("localhost:9092")
            ...     .acks("all")
            ...     .build())
            >>> from typedkafka import KafkaProducer
            >>> producer = KafkaProducer(config)
        """
        return self._config.copy()


class ConsumerConfig:
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

    def build(self) -> dict[str, Any]:
        """
        Build and return the configuration dictionary.

        Returns:
            Configuration dict ready for KafkaConsumer
        """
        return self._config.copy()
