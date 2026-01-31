"""
Kafka Consumer with comprehensive documentation and full type safety.

This module provides a well-documented, type-hinted wrapper around confluent-kafka's Consumer.
"""

import json
from collections.abc import Iterator
from typing import Any, Callable, Optional

try:
    from confluent_kafka import Consumer as ConfluentConsumer
    from confluent_kafka import KafkaError as ConfluentKafkaError
    from confluent_kafka import Message
except ImportError:
    ConfluentConsumer = None  # type: ignore[assignment,misc]
    ConfluentKafkaError = None  # type: ignore[assignment,misc]
    Message = None  # type: ignore[assignment,misc]

from typedkafka.exceptions import ConsumerError, SerializationError


class KafkaMessage:
    """
    A Kafka message with convenient access methods.

    Wraps confluent-kafka's Message with better documentation and helper methods.

    Attributes:
        topic: The topic this message came from
        partition: The partition number
        offset: The message offset
        key: The message key as bytes (None if no key)
        value: The message value as bytes
        timestamp: Message timestamp (type, value) tuple
        headers: Message headers as list of (key, value) tuples
    """

    def __init__(self, message: Any):
        """
        Initialize from a confluent-kafka Message.

        Args:
            message: A confluent_kafka.Message object
        """
        self._message = message
        self.topic = message.topic()
        self.partition = message.partition()
        self.offset = message.offset()
        self.key = message.key()
        self.value = message.value()
        self.timestamp_type, self.timestamp = message.timestamp()
        self.headers = message.headers() or []

    def value_as_string(self, encoding: str = "utf-8") -> str:
        """
        Decode the message value as a UTF-8 string.

        Args:
            encoding: Character encoding to use (default: utf-8)

        Returns:
            Decoded string value

        Raises:
            SerializationError: If decoding fails

        Examples:
            >>> msg = consumer.poll()
            >>> text = msg.value_as_string()
            >>> print(f"Received: {text}")
        """
        try:
            return self.value.decode(encoding)  # type: ignore[no-any-return]
        except (UnicodeDecodeError, AttributeError) as e:
            raise SerializationError(
                f"Failed to decode message value as {encoding} string: {e}",
                value=self.value,
                original_error=e,
            ) from e

    def value_as_json(self) -> Any:
        """
        Deserialize the message value as JSON.

        Returns:
            Parsed JSON object (dict, list, str, int, etc.)

        Raises:
            SerializationError: If JSON parsing fails

        Examples:
            >>> msg = consumer.poll()
            >>> data = msg.value_as_json()
            >>> print(f"User ID: {data['user_id']}")
        """
        try:
            return json.loads(self.value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
            raise SerializationError(
                f"Failed to deserialize message value as JSON: {e}",
                value=self.value,
                original_error=e,
            ) from e

    def key_as_string(self, encoding: str = "utf-8") -> Optional[str]:
        """
        Decode the message key as a UTF-8 string.

        Args:
            encoding: Character encoding to use (default: utf-8)

        Returns:
            Decoded string key, or None if no key

        Raises:
            SerializationError: If decoding fails

        Examples:
            >>> msg = consumer.poll()
            >>> if msg.key_as_string():
            ...     print(f"Key: {msg.key_as_string()}")
        """
        if self.key is None:
            return None
        try:
            return self.key.decode(encoding)  # type: ignore[no-any-return]
        except (UnicodeDecodeError, AttributeError) as e:
            raise SerializationError(
                f"Failed to decode message key as {encoding} string: {e}",
                value=self.key,
                original_error=e,
            ) from e

    def __repr__(self) -> str:
        """Return string representation of the message."""
        return (
            f"KafkaMessage(topic={self.topic!r}, partition={self.partition}, "
            f"offset={self.offset}, key={self.key!r})"
        )


class KafkaConsumer:
    """
    A well-documented Kafka consumer with full type hints.

    This class wraps confluent-kafka's Consumer with:
    - Comprehensive docstrings on every method
    - Full type hints for IDE autocomplete
    - Better error messages
    - Convenient message deserialization methods
    - Context manager support for automatic cleanup
    - Iterator protocol for easy message consumption

    Basic Usage:
        >>> consumer = KafkaConsumer({
        ...     "bootstrap.servers": "localhost:9092",
        ...     "group.id": "my-group",
        ...     "auto.offset.reset": "earliest"
        ... })
        >>> consumer.subscribe(["my-topic"])
        >>> for msg in consumer:
        ...     print(f"Received: {msg.value_as_string()}")

    With Context Manager:
        >>> with KafkaConsumer(config) as consumer:
        ...     consumer.subscribe(["topic"])
        ...     for msg in consumer:
        ...         process(msg)

    Attributes:
        config: The configuration dictionary used to initialize the consumer
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize a Kafka consumer with the given configuration.

        Args:
            config: Configuration dictionary for the consumer. Common options:
                - bootstrap.servers (str): Comma-separated list of broker addresses
                - group.id (str): Consumer group ID (required for subscribe())
                - client.id (str): An identifier for this client
                - auto.offset.reset (str): What to do when there's no initial offset
                  "earliest" = start from beginning, "latest" = start from end
                - enable.auto.commit (bool): Automatically commit offsets (default: True)
                - auto.commit.interval.ms (int): Frequency of offset commits in milliseconds
                - max.poll.interval.ms (int): Max time between polls before being kicked from group
                - session.timeout.ms (int): Timeout for detecting consumer failures

        Raises:
            ConsumerError: If the consumer cannot be initialized

        Examples:
            >>> # Basic consumer
            >>> consumer = KafkaConsumer({
            ...     "bootstrap.servers": "localhost:9092",
            ...     "group.id": "my-consumer-group",
            ...     "auto.offset.reset": "earliest"
            ... })

            >>> # Consumer with manual offset management
            >>> consumer = KafkaConsumer({
            ...     "bootstrap.servers": "localhost:9092",
            ...     "group.id": "my-group",
            ...     "enable.auto.commit": False
            ... })
        """
        if ConfluentConsumer is None:
            raise ImportError(
                "confluent-kafka is required. Install with: pip install confluent-kafka"
            )

        self.config = config
        self.poll_timeout: float = 1.0
        try:
            self._consumer = ConfluentConsumer(config)
        except Exception as e:
            raise ConsumerError(
                f"Failed to initialize Kafka consumer: {e}",
                original_error=e,
            ) from e

    def subscribe(
        self,
        topics: list[str],
        on_assign: Optional[Callable[[Any, Any], None]] = None,
        on_revoke: Optional[Callable[[Any, Any], None]] = None,
        on_lost: Optional[Callable[[Any, Any], None]] = None,
    ) -> None:
        """
        Subscribe to one or more topics.

        Args:
            topics: List of topic names to subscribe to
            on_assign: Callback invoked when partitions are assigned.
                Signature: callback(consumer, partitions)
            on_revoke: Callback invoked when partitions are revoked.
                Signature: callback(consumer, partitions)
            on_lost: Callback invoked when partitions are lost (unclean).
                Signature: callback(consumer, partitions)

        Raises:
            ConsumerError: If subscription fails

        Examples:
            >>> # Subscribe to a single topic
            >>> consumer.subscribe(["my-topic"])

            >>> # Subscribe to multiple topics
            >>> consumer.subscribe(["orders", "payments", "shipments"])

            >>> # Subscribe with rebalance callbacks
            >>> def on_assign(consumer, partitions):
            ...     print(f"Assigned: {partitions}")
            >>> def on_revoke(consumer, partitions):
            ...     print(f"Revoked: {partitions}")
            >>> consumer.subscribe(["my-topic"], on_assign=on_assign, on_revoke=on_revoke)
        """
        try:
            kwargs: dict[str, Any] = {}
            if on_assign is not None:
                kwargs["on_assign"] = on_assign
            if on_revoke is not None:
                kwargs["on_revoke"] = on_revoke
            if on_lost is not None:
                kwargs["on_lost"] = on_lost
            self._consumer.subscribe(topics, **kwargs)
        except Exception as e:
            raise ConsumerError(
                f"Failed to subscribe to topics {topics}: {e}",
                original_error=e,
            ) from e

    def poll(self, timeout: float = 1.0) -> Optional[KafkaMessage]:
        """
        Poll for a single message.

        Args:
            timeout: Maximum time to wait for a message in seconds (default: 1.0)

        Returns:
            KafkaMessage if a message was received, None if timeout expired

        Raises:
            ConsumerError: If an error occurs during polling

        Examples:
            >>> # Poll with default 1 second timeout
            >>> msg = consumer.poll()
            >>> if msg:
            ...     print(f"Received: {msg.value_as_string()}")

            >>> # Poll with longer timeout
            >>> msg = consumer.poll(timeout=5.0)

            >>> # Poll in a loop
            >>> while True:
            ...     msg = consumer.poll(timeout=1.0)
            ...     if msg:
            ...         process(msg)
            ...         consumer.commit(msg)
        """
        try:
            raw_msg = self._consumer.poll(timeout=timeout)
            if raw_msg is None:
                return None
            if raw_msg.error():
                raise ConsumerError(f"Consumer error: {raw_msg.error()}")
            return KafkaMessage(raw_msg)
        except ConsumerError:
            raise
        except Exception as e:
            raise ConsumerError(
                f"Error while polling: {e}",
                original_error=e,
            ) from e

    def commit(self, message: Optional[KafkaMessage] = None, asynchronous: bool = True) -> None:
        """
        Commit offsets to Kafka.

        Args:
            message: Specific message to commit. If None, commits all consumed messages.
            asynchronous: If True, commit asynchronously (default). If False, wait for confirmation.

        Raises:
            ConsumerError: If commit fails

        Examples:
            >>> # Commit after processing each message
            >>> msg = consumer.poll()
            >>> if msg:
            ...     process(msg)
            ...     consumer.commit(msg)

            >>> # Commit all consumed messages
            >>> consumer.commit()

            >>> # Synchronous commit (wait for confirmation)
            >>> consumer.commit(msg, asynchronous=False)
        """
        try:
            if message:
                self._consumer.commit(message=message._message, asynchronous=asynchronous)  # type: ignore[call-overload]
            else:
                self._consumer.commit(asynchronous=asynchronous)  # type: ignore[call-overload]
        except Exception as e:
            raise ConsumerError(
                f"Failed to commit offsets: {e}",
                original_error=e,
            ) from e

    def close(self) -> None:
        """
        Close the consumer and leave the consumer group.

        It's recommended to use the consumer as a context manager instead of calling
        this method directly.

        Examples:
            >>> consumer = KafkaConsumer(config)
            >>> try:
            ...     consumer.subscribe(["topic"])
            ...     for msg in consumer:
            ...         process(msg)
            ... finally:
            ...     consumer.close()

            >>> # Better: use context manager
            >>> with KafkaConsumer(config) as consumer:
            ...     consumer.subscribe(["topic"])
            ...     for msg in consumer:
            ...         process(msg)
        """
        try:
            self._consumer.close()
        except Exception as e:
            raise ConsumerError(
                f"Failed to close consumer: {e}",
                original_error=e,
            ) from e

    def __iter__(self) -> Iterator[KafkaMessage]:
        """
        Iterate over messages indefinitely.

        Uses the configured poll_timeout (default 1.0s). Configure via the
        poll_timeout property.

        Yields:
            KafkaMessage objects as they arrive

        Examples:
            >>> for msg in consumer:
            ...     print(f"Received: {msg.value_as_string()}")
            ...     consumer.commit(msg)

            >>> # With custom poll timeout
            >>> consumer.poll_timeout = 5.0
            >>> for msg in consumer:
            ...     process(msg)
        """
        while True:
            msg = self.poll(timeout=self.poll_timeout)
            if msg:
                yield msg

    def __enter__(self) -> "KafkaConsumer":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup resources."""
        self.close()
