"""
Kafka Producer with comprehensive documentation and full type safety.

This module provides a well-documented, type-hinted wrapper around confluent-kafka's Producer.
"""

import json
from typing import Any, Callable, Optional

try:
    from confluent_kafka import KafkaError as ConfluentKafkaError
    from confluent_kafka import Producer as ConfluentProducer
except ImportError:
    # Make confluent-kafka optional for documentation/type checking
    ConfluentProducer = None  # type: ignore[assignment,misc]
    ConfluentKafkaError = None  # type: ignore[assignment,misc]

from typedkafka.exceptions import ProducerError, SerializationError


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

    def __init__(self, config: dict[str, Any]):
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

        Raises:
            ProducerError: If the producer cannot be initialized with the given config

        Examples:
            >>> # Basic producer
            >>> producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})

            >>> # Producer with compression
            >>> producer = KafkaProducer({
            ...     "bootstrap.servers": "localhost:9092",
            ...     "compression.type": "gzip",
            ...     "acks": "all"
            ... })
        """
        if ConfluentProducer is None:
            raise ImportError(
                "confluent-kafka is required. Install with: pip install confluent-kafka"
            )

        self.config = config
        try:
            self._producer = ConfluentProducer(config)
        except Exception as e:
            raise ProducerError(
                f"Failed to initialize Kafka producer: {e}",
                original_error=e,
            ) from e

    def send(
        self,
        topic: str,
        value: bytes,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        on_delivery: Optional[Callable[[Any, Any], None]] = None,
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

        Raises:
            ProducerError: If the message cannot be queued (e.g., queue is full)

        Examples:
            >>> # Send a simple message
            >>> producer.send("my-topic", b"Hello, Kafka!")

            >>> # Send with a key for partitioning
            >>> producer.send("user-events", b"event data", key=b"user-123")

            >>> # Send to a specific partition
            >>> producer.send("my-topic", b"data", partition=0)

            >>> # Send with delivery callback
            >>> def on_delivery(err, msg):
            ...     if err:
            ...         print(f"Delivery failed: {err}")
            ...     else:
            ...         print(f"Delivered to {msg.topic()} [{msg.partition()}]")
            >>> producer.send("topic", b"data", on_delivery=on_delivery)
        """
        try:
            self._producer.produce(
                topic=topic,
                value=value,
                key=key,
                partition=partition,  # type: ignore[arg-type]
                on_delivery=on_delivery,
            )
            # Poll to trigger callbacks and handle backpressure
            self._producer.poll(0)
        except BufferError as e:
            raise ProducerError(
                "Message queue is full. Try calling flush() or increasing queue.buffering.max.messages",
                original_error=e,
            ) from e
        except Exception as e:
            raise ProducerError(
                f"Failed to send message to topic '{topic}': {e}",
                original_error=e,
            ) from e

    def send_json(
        self,
        topic: str,
        value: Any,
        key: Optional[str] = None,
        partition: Optional[int] = None,
        on_delivery: Optional[Callable[[Any, Any], None]] = None,
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
        key: Optional[str] = None,
        partition: Optional[int] = None,
        on_delivery: Optional[Callable[[Any, Any], None]] = None,
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

    def __enter__(self) -> "KafkaProducer":
        """
        Enter context manager.

        Returns:
            self

        Examples:
            >>> with KafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
            ...     producer.send("topic", b"message")
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager and cleanup resources.

        Automatically flushes all pending messages before exiting.
        """
        self.close()
