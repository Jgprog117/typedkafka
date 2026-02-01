"""
Kafka Producer with comprehensive documentation and full type safety.

This module provides a well-documented, type-hinted wrapper around confluent-kafka's Producer.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar

if TYPE_CHECKING:
    from typedkafka.logging import KafkaLogger
    from typedkafka.topics import TypedTopic

T = TypeVar("T")

try:
    from confluent_kafka import KafkaError as ConfluentKafkaError
    from confluent_kafka import Producer as ConfluentProducer
except ImportError:
    # Make confluent-kafka optional for documentation/type checking
    ConfluentProducer = None  # type: ignore[assignment,misc]
    ConfluentKafkaError = None  # type: ignore[assignment,misc]

from typedkafka.exceptions import ProducerError, SerializationError, TransactionError
from typedkafka.metrics import KafkaMetrics, StatsCallback, make_stats_cb

#: Type alias for delivery report callbacks.
#: The callback receives an optional error and the message object.
DeliveryCallback = Callable[[Optional[Any], Any], None]


class KafkaProducer:
    """
    A well-documented Kafka producer with full type hints.

    This class wraps confluent-kafka's Producer with:
    - Comprehensive docstrings on every method
    - Full type hints for IDE autocomplete
    - Better error messages
    - Convenient methods for common operations (send_json, send_string)
    - Context manager support for automatic cleanup

    Basic Usage:
        >>> producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
        >>> producer.send("my-topic", b"my message", key=b"my-key")
        >>> producer.flush()  # Wait for all messages to be delivered

    With Context Manager:
        >>> with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
        ...     producer.send("my-topic", b"message")
        ...     # Automatic flush and cleanup on exit

    JSON Messages:
        >>> producer.send_json("events", {"user_id": 123, "action": "click"})

    Attributes:
        config: The configuration dictionary used to initialize the producer
    """

    def __init__(
        self,
        config: dict[str, Any],
        on_stats: StatsCallback | None = None,
        logger: KafkaLogger | None = None,
    ):
        """
        Initialize a Kafka producer with the given configuration.

        Args:
            config: Configuration dictionary for the producer. Common options:
                - bootstrap.servers (str): Comma-separated list of broker addresses
                  Example: "localhost:9092" or "broker1:9092,broker2:9092"
                - client.id (str): An identifier for this client
                - acks (str|int): Number of acknowledgments the producer requires
                  "0" = no acknowledgment, "1" = leader only, "all" = all replicas
                - compression.type (str): Compression codec ("none", "gzip", "snappy", "lz4", "zstd")
                - max.in.flight.requests.per.connection (int): Max unacknowledged requests
                - linger.ms (int): Time to wait before sending a batch
                - batch.size (int): Maximum size of a message batch in bytes
                - statistics.interval.ms (int): Stats reporting interval in milliseconds
            on_stats: Optional callback receiving parsed KafkaStats each reporting interval.
                Requires ``statistics.interval.ms`` to be set in config.
            logger: Optional KafkaLogger for structured logging of producer operations.

        Raises:
            ProducerError: If the producer cannot be initialized with the given config

        Examples:
            >>> # Basic producer
            >>> producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})

            >>> # Producer with metrics
            >>> producer = KafkaProducer({
            ...     "bootstrap.servers": "localhost:9092",
            ...     "statistics.interval.ms": 5000,
            ... })
            >>> print(producer.metrics.messages_sent)
        """
        if ConfluentProducer is None:
            raise ImportError(
                "confluent-kafka is required. Install with: pip install confluent-kafka"
            )

        self._metrics = KafkaMetrics()
        self._logger = logger
        self.config = config
        # Inject stats callback if stats interval is configured
        if config.get("statistics.interval.ms"):
            config = dict(config)
            config["stats_cb"] = make_stats_cb(self._metrics, on_stats)
        try:
            self._producer = ConfluentProducer(config)
        except Exception as e:
            raise ProducerError(
                f"Failed to initialize Kafka producer: {e}",
                original_error=e,
            ) from e

    @property
    def metrics(self) -> KafkaMetrics:
        """Current metrics for this producer.

        Tracks messages sent, errors, and (if stats enabled) byte throughput.
        """
        return self._metrics

    def send(
        self,
        topic: str,
        value: bytes,
        key: bytes | None = None,
        partition: int | None = None,
        on_delivery: DeliveryCallback | None = None,
        headers: list[tuple[str, bytes]] | None = None,
    ) -> None:
        """
        Send a message to a Kafka topic.

        This method is asynchronous - it returns immediately after queuing the message.
        Use flush() to wait for delivery confirmation.

        Args:
            topic: The topic name to send the message to
            value: The message payload as bytes
            key: Optional message key as bytes. Messages with the same key go to the same partition.
            partition: Optional partition number. If None, partition is chosen by the partitioner.
            on_delivery: Optional callback function called when delivery succeeds or fails.
                Signature: callback(error, message)
            headers: Optional list of (key, value) header tuples to include with the message.

        Raises:
            ProducerError: If the message cannot be queued (e.g., queue is full)

        Examples:
            >>> # Send a simple message
            >>> producer.send("my-topic", b"Hello, Kafka!")

            >>> # Send with a key for partitioning
            >>> producer.send("user-events", b"event data", key=b"user-123")

            >>> # Send with headers
            >>> producer.send("topic", b"data", headers=[("trace-id", b"abc123")])
        """
        try:
            kwargs: dict[str, Any] = {
                "topic": topic,
                "value": value,
                "key": key,
            }
            if partition is not None:
                kwargs["partition"] = partition
            if on_delivery is not None:
                kwargs["on_delivery"] = on_delivery
            if headers is not None:
                kwargs["headers"] = headers
            self._producer.produce(**kwargs)  # type: ignore[arg-type]
            # Poll to trigger callbacks and handle backpressure
            self._producer.poll(0)
            self._metrics.messages_sent += 1
            if self._logger:
                self._logger.log_send(
                    topic=topic,
                    key=key.decode("utf-8", errors="replace") if key else None,
                    partition=partition,
                )
        except BufferError as e:
            self._metrics.errors += 1
            raise ProducerError(
                "Message queue is full. Try calling flush() or increasing queue.buffering.max.messages",
                original_error=e,
            ) from e
        except Exception as e:
            self._metrics.errors += 1
            raise ProducerError(
                f"Failed to send message to topic '{topic}': {e}",
                original_error=e,
            ) from e

    def send_json(
        self,
        topic: str,
        value: Any,
        key: str | None = None,
        partition: int | None = None,
        on_delivery: DeliveryCallback | None = None,
    ) -> None:
        """
        Send a JSON-serialized message to a Kafka topic.

        Convenience method that automatically serializes Python objects to JSON.

        Args:
            topic: The topic name to send the message to
            value: Any JSON-serializable Python object (dict, list, str, int, etc.)
            key: Optional string key (will be UTF-8 encoded)
            partition: Optional partition number
            on_delivery: Optional callback function for delivery confirmation

        Raises:
            SerializationError: If the value cannot be serialized to JSON
            ProducerError: If the message cannot be queued

        Examples:
            >>> # Send a dict as JSON
            >>> producer.send_json("events", {"user_id": 123, "action": "click"})

            >>> # Send with a string key
            >>> producer.send_json("user-data", {"name": "Alice"}, key="user-123")

            >>> # Send a list
            >>> producer.send_json("numbers", [1, 2, 3, 4, 5])
        """
        try:
            value_bytes = json.dumps(value).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise SerializationError(
                f"Failed to serialize value to JSON: {e}",
                value=value,
                original_error=e,
            ) from e

        key_bytes = key.encode("utf-8") if key is not None else None
        self.send(topic, value_bytes, key=key_bytes, partition=partition, on_delivery=on_delivery)

    def send_string(
        self,
        topic: str,
        value: str,
        key: str | None = None,
        partition: int | None = None,
        on_delivery: DeliveryCallback | None = None,
    ) -> None:
        """
        Send a UTF-8 encoded string message to a Kafka topic.

        Convenience method for sending text messages.

        Args:
            topic: The topic name to send the message to
            value: String message to send
            key: Optional string key
            partition: Optional partition number
            on_delivery: Optional callback function for delivery confirmation

        Raises:
            ProducerError: If the message cannot be queued

        Examples:
            >>> producer.send_string("logs", "Application started successfully")
            >>> producer.send_string("user-messages", "Hello!", key="user-123")
        """
        value_bytes = value.encode("utf-8")
        key_bytes = key.encode("utf-8") if key is not None else None
        self.send(topic, value_bytes, key=key_bytes, partition=partition, on_delivery=on_delivery)

    def send_typed(
        self,
        topic: TypedTopic[T],
        value: T,
        key: Any | None = None,
        partition: int | None = None,
        on_delivery: DeliveryCallback | None = None,
        headers: list[tuple[str, bytes]] | None = None,
    ) -> None:
        """
        Send a message to a typed topic using its configured serializers.

        Provides compile-time type safety: the IDE will verify that ``value``
        matches the topic's type parameter.

        Args:
            topic: A TypedTopic that specifies serialization.
            value: The message value (must match the topic's type parameter).
            key: Optional message key. Requires the topic to have a key_serializer.
            partition: Optional partition number.
            on_delivery: Optional delivery report callback.
            headers: Optional message headers.

        Raises:
            SerializationError: If serialization fails or key provided without key_serializer.
            ProducerError: If the message cannot be queued.

        Examples:
            >>> from typedkafka.topics import json_topic, string_topic
            >>> events = json_topic("events")
            >>> producer.send_typed(events, {"user_id": 123, "action": "click"})
            >>>
            >>> logs = string_topic("logs")
            >>> producer.send_typed(logs, "Application started")
        """
        try:
            value_bytes = topic.value_serializer.serialize(topic.name, value)
        except Exception as e:
            self._metrics.errors += 1
            raise SerializationError(
                f"Failed to serialize value for topic '{topic.name}': {e}",
                value=value,
                original_error=e,
            ) from e

        key_bytes: bytes | None = None
        if key is not None:
            if topic.key_serializer is None:
                raise SerializationError(
                    f"Topic '{topic.name}' has no key_serializer configured but a key was provided",
                    value=key,
                )
            try:
                key_bytes = topic.key_serializer.serialize(topic.name, key)
            except Exception as e:
                self._metrics.errors += 1
                raise SerializationError(
                    f"Failed to serialize key for topic '{topic.name}': {e}",
                    value=key,
                    original_error=e,
                ) from e

        self.send(
            topic.name,
            value_bytes,
            key=key_bytes,
            partition=partition,
            on_delivery=on_delivery,
            headers=headers,
        )

    def flush(self, timeout: float = -1) -> int:
        """
        Wait for all messages in the queue to be delivered.

        Blocks until all messages are sent or the timeout expires.

        Args:
            timeout: Maximum time to wait in seconds. Use -1 for infinite wait (default).
                Example: 5.0 = wait up to 5 seconds

        Returns:
            Number of messages still in queue/internal Producer state. 0 means all delivered.

        Raises:
            ProducerError: If flush fails

        Examples:
            >>> # Wait for all messages to be delivered
            >>> producer.send("topic", b"message 1")
            >>> producer.send("topic", b"message 2")
            >>> remaining = producer.flush()
            >>> if remaining == 0:
            ...     print("All messages delivered successfully")

            >>> # Wait up to 5 seconds
            >>> remaining = producer.flush(timeout=5.0)
            >>> if remaining > 0:
            ...     print(f"Warning: {remaining} messages not delivered after 5 seconds")
        """
        try:
            return self._producer.flush(timeout=timeout)  # type: ignore[no-any-return]
        except Exception as e:
            raise ProducerError(f"Flush failed: {e}", original_error=e) from e

    def close(self) -> None:
        """
        Close the producer and release resources.

        Calls flush() to ensure all queued messages are delivered before closing.
        It's recommended to use the producer as a context manager instead of calling
        this method directly.

        Examples:
            >>> producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
            >>> try:
            ...     producer.send("topic", b"message")
            ... finally:
            ...     producer.close()  # Ensure cleanup

            >>> # Better: use context manager
            >>> with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
            ...     producer.send("topic", b"message")
        """
        self.flush()

    def __enter__(self) -> KafkaProducer:
        """
        Enter context manager.

        Returns:
            self

        Examples:
            >>> with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
            ...     producer.send("topic", b"message")
        """
        return self

    def send_batch(
        self,
        topic: str,
        messages: list[tuple[bytes, bytes | None]],
        on_delivery: DeliveryCallback | None = None,
    ) -> None:
        """
        Send a batch of messages to a Kafka topic.

        Each message is a tuple of (value, key). This is more efficient than
        calling send() repeatedly as it defers polling until after all messages
        are queued.

        Args:
            topic: The topic name to send the messages to
            messages: List of (value, key) tuples. Key can be None.
            on_delivery: Optional callback for each message delivery.

        Raises:
            ProducerError: If any message cannot be queued

        Examples:
            >>> producer.send_batch("events", [
            ...     (b"event1", b"key1"),
            ...     (b"event2", b"key2"),
            ...     (b"event3", None),
            ... ])
            >>> producer.flush()
        """
        for value, key in messages:
            try:
                self._producer.produce(
                    topic=topic,
                    value=value,
                    key=key,
                    on_delivery=on_delivery,
                )
            except BufferError:
                # Flush and retry once on buffer full
                self._producer.flush()
                try:
                    self._producer.produce(
                        topic=topic,
                        value=value,
                        key=key,
                        on_delivery=on_delivery,
                    )
                except Exception as retry_e:
                    raise ProducerError(
                        f"Failed to send message to topic '{topic}' after flush: {retry_e}",
                        original_error=retry_e,
                    ) from retry_e
            except Exception as e:
                raise ProducerError(
                    f"Failed to send message to topic '{topic}': {e}",
                    original_error=e,
                ) from e
        # Poll to trigger callbacks
        self._producer.poll(0)

    def init_transactions(self, timeout: float = 30.0) -> None:
        """
        Initialize the producer for transactions.

        Must be called before any transactional methods. Requires the
        ``transactional.id`` configuration to be set.

        Args:
            timeout: Maximum time to wait for initialization in seconds.

        Raises:
            TransactionError: If transaction initialization fails.

        Examples:
            >>> producer = KafkaProducer({
            ...     "bootstrap.servers": "localhost:9092",
            ...     "transactional.id": "my-txn-id",
            ... })
            >>> producer.init_transactions()
        """
        try:
            self._producer.init_transactions(timeout)
        except Exception as e:
            raise TransactionError(
                f"Failed to initialize transactions: {e}",
                original_error=e,
            ) from e

    def begin_transaction(self) -> None:
        """
        Begin a new transaction.

        Raises:
            TransactionError: If beginning the transaction fails.
        """
        try:
            self._producer.begin_transaction()
            if self._logger:
                self._logger.log_transaction("begin")
        except Exception as e:
            raise TransactionError(
                f"Failed to begin transaction: {e}",
                original_error=e,
            ) from e

    def commit_transaction(self, timeout: float = 30.0) -> None:
        """
        Commit the current transaction.

        Args:
            timeout: Maximum time to wait for commit in seconds.

        Raises:
            TransactionError: If committing the transaction fails.
        """
        try:
            self._producer.commit_transaction(timeout)
            if self._logger:
                self._logger.log_transaction("commit")
        except Exception as e:
            raise TransactionError(
                f"Failed to commit transaction: {e}",
                original_error=e,
            ) from e

    def abort_transaction(self, timeout: float = 30.0) -> None:
        """
        Abort the current transaction.

        Args:
            timeout: Maximum time to wait for abort in seconds.

        Raises:
            TransactionError: If aborting the transaction fails.
        """
        try:
            self._producer.abort_transaction(timeout)
            if self._logger:
                self._logger.log_transaction("abort")
        except Exception as e:
            raise TransactionError(
                f"Failed to abort transaction: {e}",
                original_error=e,
            ) from e

    def transaction(self) -> TransactionContext:
        """
        Return a context manager for transactional sends.

        Automatically begins, commits, or aborts the transaction.

        Returns:
            A context manager that manages the transaction lifecycle.

        Raises:
            ProducerError: If any transaction operation fails.

        Examples:
            >>> producer = KafkaProducer({
            ...     "bootstrap.servers": "localhost:9092",
            ...     "transactional.id": "my-txn-id",
            ... })
            >>> producer.init_transactions()
            >>> with producer.transaction():
            ...     producer.send("topic", b"msg1")
            ...     producer.send("topic", b"msg2")
        """
        return TransactionContext(self)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager and cleanup resources.

        Automatically flushes all pending messages before exiting.
        """
        self.close()


class TransactionContext:
    """Context manager for Kafka transactions.

    Begins a transaction on entry and commits on clean exit.
    Aborts the transaction if an exception occurs.
    """

    def __init__(self, producer: KafkaProducer):
        self._producer = producer

    def __enter__(self) -> TransactionContext:
        self._producer.begin_transaction()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self._producer.abort_transaction()
        else:
            self._producer.commit_transaction()
