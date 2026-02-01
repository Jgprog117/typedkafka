"""
Testing utilities for typedkafka - Mock producer and consumer for unit tests.

This module provides mock implementations that don't require a running Kafka broker,
making it easy to write fast, reliable unit tests for code that uses Kafka.
"""

import json as _json
from collections import defaultdict
from typing import Any, Callable, Optional

#: Type alias for delivery report callbacks (matches producer.DeliveryCallback).
DeliveryCallback = Callable[[Optional[Any], Any], None]


class MockMessage:
    """
    A mock Kafka message for testing.

    Attributes:
        topic: The topic this message was sent to
        value: The message value
        key: The message key (optional)
        partition: The partition number
        offset: The message offset
        headers: Message headers
    """

    def __init__(
        self,
        topic: str,
        value: bytes,
        key: Optional[bytes] = None,
        partition: int = 0,
        offset: int = 0,
        headers: Optional[list[tuple[str, bytes]]] = None,
    ):
        """
        Initialize a mock message.

        Args:
            topic: Topic name
            value: Message value as bytes
            key: Optional message key
            partition: Partition number (default: 0)
            offset: Message offset (default: 0)
            headers: Optional list of (key, value) header tuples
        """
        self.topic = topic
        self.value = value
        self.key = key
        self.partition = partition
        self.offset = offset
        self.headers = headers or []
        self.timestamp_type = 0
        self.timestamp = 0

    def value_as_string(self, encoding: str = "utf-8") -> str:
        """
        Decode the message value as a string.

        Args:
            encoding: Character encoding to use (default: utf-8)

        Returns:
            Decoded string value

        Raises:
            SerializationError: If decoding fails
        """
        from typedkafka.exceptions import SerializationError

        try:
            return self.value.decode(encoding)
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
            Parsed JSON object

        Raises:
            SerializationError: If JSON parsing fails
        """
        from typedkafka.exceptions import SerializationError

        try:
            return _json.loads(self.value.decode("utf-8"))
        except (_json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
            raise SerializationError(
                f"Failed to deserialize message value as JSON: {e}",
                value=self.value,
                original_error=e,
            ) from e

    def key_as_string(self, encoding: str = "utf-8") -> Optional[str]:
        """
        Decode the message key as a string.

        Args:
            encoding: Character encoding to use (default: utf-8)

        Returns:
            Decoded string key, or None if no key
        """
        if self.key is None:
            return None
        from typedkafka.exceptions import SerializationError

        try:
            return self.key.decode(encoding)
        except (UnicodeDecodeError, AttributeError) as e:
            raise SerializationError(
                f"Failed to decode message key as {encoding} string: {e}",
                value=self.key,
                original_error=e,
            ) from e

    def __repr__(self) -> str:
        """Return string representation of the message."""
        return (
            f"MockMessage(topic={self.topic!r}, partition={self.partition}, "
            f"offset={self.offset}, key={self.key!r})"
        )


class MockProducer:
    """
    A mock Kafka producer for testing.

    Records all messages sent to topics without actually sending to Kafka.
    Perfect for unit tests to verify your code sends the right messages.

    Examples:
        >>> producer = MockProducer()
        >>> producer.send("my-topic", b"test message", key=b"test-key")
        >>>
        >>> # Verify the message was sent
        >>> assert len(producer.messages["my-topic"]) == 1
        >>> msg = producer.messages["my-topic"][0]
        >>> assert msg.value == b"test message"
        >>> assert msg.key == b"test-key"

    Attributes:
        messages: Dict mapping topic names to lists of MockMessage objects
        call_count: Number of times send() was called
        flushed: Whether flush() has been called
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize a mock producer.

        Args:
            config: Optional config dict (ignored, but accepted for compatibility)
        """
        self.config = config or {}
        self.messages: dict[str, list[MockMessage]] = defaultdict(list)
        self.call_count = 0
        self.flushed = False
        self._closed = False
        self._in_transaction = False
        self._transaction_messages: list[tuple[str, MockMessage]] = []

    def send(
        self,
        topic: str,
        value: bytes,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        on_delivery: Optional[DeliveryCallback] = None,
    ) -> None:
        """
        Record a message send (doesn't actually send to Kafka).

        Args:
            topic: Topic to send to
            value: Message value
            key: Optional message key
            partition: Optional partition (default: 0)
            on_delivery: Optional callback (will be called immediately with success)

        Examples:
            >>> producer = MockProducer()
            >>> producer.send("events", b"data", key=b"key-1")
            >>> assert len(producer.messages["events"]) == 1
        """
        self.call_count += 1
        offset = len(self.messages[topic])

        msg = MockMessage(
            topic=topic,
            value=value,
            key=key,
            partition=partition or 0,
            offset=offset,
        )

        if self._in_transaction:
            self._transaction_messages.append((topic, msg))
        else:
            self.messages[topic].append(msg)

        # Call delivery callback with success
        if on_delivery:
            on_delivery(None, msg)

    def send_json(
        self,
        topic: str,
        value: Any,
        key: Optional[str] = None,
        partition: Optional[int] = None,
        on_delivery: Optional[DeliveryCallback] = None,
    ) -> None:
        """
        Record a JSON message send.

        Args:
            topic: Topic to send to
            value: JSON-serializable value
            key: Optional string key
            partition: Optional partition
            on_delivery: Optional delivery callback

        Examples:
            >>> producer = MockProducer()
            >>> producer.send_json("events", {"user_id": 123})
            >>> import json
            >>> data = json.loads(producer.messages["events"][0].value)
            >>> assert data["user_id"] == 123
        """
        value_bytes = _json.dumps(value).encode("utf-8")
        key_bytes = key.encode("utf-8") if key else None
        self.send(topic, value_bytes, key=key_bytes, partition=partition, on_delivery=on_delivery)

    def send_string(
        self,
        topic: str,
        value: str,
        key: Optional[str] = None,
        partition: Optional[int] = None,
        on_delivery: Optional[DeliveryCallback] = None,
    ) -> None:
        """
        Record a string message send.

        Args:
            topic: Topic to send to
            value: String value
            key: Optional string key
            partition: Optional partition
            on_delivery: Optional delivery callback
        """
        value_bytes = value.encode("utf-8")
        key_bytes = key.encode("utf-8") if key else None
        self.send(topic, value_bytes, key=key_bytes, partition=partition, on_delivery=on_delivery)

    def send_batch(
        self,
        topic: str,
        messages: list[tuple[bytes, Optional[bytes]]],
        on_delivery: Optional[DeliveryCallback] = None,
    ) -> None:
        """
        Record a batch of message sends.

        Args:
            topic: Topic to send to
            messages: List of (value, key) tuples
            on_delivery: Optional delivery callback
        """
        for value, key in messages:
            self.send(topic, value, key=key, on_delivery=on_delivery)

    def flush(self, timeout: float = -1) -> int:
        """
        Mark producer as flushed (no-op in mock).

        Args:
            timeout: Ignored in mock

        Returns:
            0 (always successful in mock)

        Examples:
            >>> producer = MockProducer()
            >>> producer.send("topic", b"msg")
            >>> remaining = producer.flush()
            >>> assert remaining == 0
            >>> assert producer.flushed is True
        """
        self.flushed = True
        return 0

    def close(self) -> None:
        """Mark producer as closed."""
        self._closed = True
        self.flush()

    def init_transactions(self, timeout: float = 30.0) -> None:
        """Initialize transactions (no-op in mock)."""
        pass

    def begin_transaction(self) -> None:
        """Begin a mock transaction."""
        self._in_transaction = True
        self._transaction_messages = []

    def commit_transaction(self, timeout: float = 30.0) -> None:
        """Commit the mock transaction, flushing buffered messages."""
        for topic, msg in self._transaction_messages:
            self.messages[topic].append(msg)
        self._transaction_messages = []
        self._in_transaction = False

    def abort_transaction(self, timeout: float = 30.0) -> None:
        """Abort the mock transaction, discarding buffered messages."""
        self._transaction_messages = []
        self._in_transaction = False

    def transaction(self) -> "MockTransactionContext":
        """Return a mock transaction context manager."""
        return MockTransactionContext(self)

    def reset(self) -> None:
        """
        Clear all recorded messages and reset state.

        Useful for reusing the same mock across multiple test cases.

        Examples:
            >>> producer = MockProducer()
            >>> producer.send("topic", b"msg1")
            >>> producer.reset()
            >>> assert len(producer.messages) == 0
            >>> assert producer.call_count == 0
        """
        self.messages.clear()
        self.call_count = 0
        self.flushed = False
        self._closed = False
        self._in_transaction = False
        self._transaction_messages = []

    def __enter__(self) -> "MockProducer":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


class MockTransactionContext:
    """Mock transaction context manager for testing."""

    def __init__(self, producer: MockProducer):
        self._producer = producer

    def __enter__(self) -> "MockTransactionContext":
        self._producer.begin_transaction()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self._producer.abort_transaction()
        else:
            self._producer.commit_transaction()


class MockConsumer:
    """
    A mock Kafka consumer for testing.

    Allows you to inject predefined messages for testing code that consumes from Kafka.

    Examples:
        >>> consumer = MockConsumer()
        >>> consumer.add_message("my-topic", b"test message", key=b"test-key")
        >>> consumer.subscribe(["my-topic"])
        >>>
        >>> msg = consumer.poll()
        >>> assert msg.value == b"test message"
        >>> assert msg.key == b"test-key"

    Attributes:
        messages: Queue of MockMessage objects to be consumed
        subscribed_topics: List of subscribed topics
        committed_offsets: Dict of committed offsets by topic/partition
        poll_timeout: Timeout used by __iter__ (matches KafkaConsumer)
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize a mock consumer.

        Args:
            config: Optional config dict (ignored, but accepted for compatibility)
        """
        self.config = config or {}
        self.messages: list[MockMessage] = []
        self.subscribed_topics: list[str] = []
        self.committed_offsets: dict[tuple[str, int], int] = {}
        self._closed = False
        self._message_index = 0
        self.poll_timeout: float = 1.0
        self._assignment: list[Any] = []

    def add_message(
        self,
        topic: str,
        value: bytes,
        key: Optional[bytes] = None,
        partition: int = 0,
        offset: Optional[int] = None,
        headers: Optional[list[tuple[str, bytes]]] = None,
    ) -> None:
        """
        Add a message to be consumed.

        Call this in your tests to inject messages that your code will consume.

        Args:
            topic: Topic name
            value: Message value
            key: Optional message key
            partition: Partition number (default: 0)
            offset: Message offset (auto-generated if None)
            headers: Optional message headers

        Examples:
            >>> consumer = MockConsumer()
            >>> consumer.add_message("events", b'{"user_id": 123}')
            >>> consumer.add_message("events", b'{"user_id": 456}')
            >>> assert len(consumer.messages) == 2
        """
        if offset is None:
            offset = len(self.messages)

        msg = MockMessage(
            topic=topic,
            value=value,
            key=key,
            partition=partition,
            offset=offset,
            headers=headers,
        )
        self.messages.append(msg)

    def add_json_message(
        self,
        topic: str,
        value: Any,
        key: Optional[str] = None,
        partition: int = 0,
    ) -> None:
        """
        Add a JSON message to be consumed.

        Args:
            topic: Topic name
            value: JSON-serializable value
            key: Optional string key
            partition: Partition number

        Examples:
            >>> consumer = MockConsumer()
            >>> consumer.add_json_message("events", {"user_id": 123, "action": "click"})
        """
        value_bytes = _json.dumps(value).encode("utf-8")
        key_bytes = key.encode("utf-8") if key else None
        self.add_message(topic, value_bytes, key=key_bytes, partition=partition)

    def subscribe(
        self,
        topics: list[str],
        on_assign: Optional[DeliveryCallback] = None,
        on_revoke: Optional[DeliveryCallback] = None,
        on_lost: Optional[DeliveryCallback] = None,
    ) -> None:
        """
        Subscribe to topics (recorded but not enforced in mock).

        Args:
            topics: List of topic names
            on_assign: Optional rebalance callback (stored but not called in mock)
            on_revoke: Optional rebalance callback (stored but not called in mock)
            on_lost: Optional rebalance callback (stored but not called in mock)

        Examples:
            >>> consumer = MockConsumer()
            >>> consumer.subscribe(["topic1", "topic2"])
            >>> assert "topic1" in consumer.subscribed_topics
        """
        self.subscribed_topics = topics
        self._on_assign = on_assign
        self._on_revoke = on_revoke
        self._on_lost = on_lost

    def poll(self, timeout: float = 1.0) -> Optional[MockMessage]:
        """
        Poll for the next message.

        Returns messages in the order they were added with add_message().

        Args:
            timeout: Ignored in mock

        Returns:
            Next MockMessage or None if no more messages

        Examples:
            >>> consumer = MockConsumer()
            >>> consumer.add_message("topic", b"msg1")
            >>> consumer.add_message("topic", b"msg2")
            >>>
            >>> msg1 = consumer.poll()
            >>> assert msg1.value == b"msg1"
            >>> msg2 = consumer.poll()
            >>> assert msg2.value == b"msg2"
            >>> msg3 = consumer.poll()
            >>> assert msg3 is None
        """
        if self._message_index < len(self.messages):
            msg = self.messages[self._message_index]
            self._message_index += 1
            return msg
        return None

    def commit(
        self, message: Optional[MockMessage] = None, asynchronous: bool = True
    ) -> None:
        """
        Record a commit (doesn't actually commit to Kafka).

        Args:
            message: Message to commit offset for
            asynchronous: Ignored in mock

        Examples:
            >>> consumer = MockConsumer()
            >>> consumer.add_message("topic", b"msg", partition=0, offset=42)
            >>> msg = consumer.poll()
            >>> consumer.commit(msg)
            >>> assert consumer.committed_offsets[("topic", 0)] == 42
        """
        if message:
            key = (message.topic, message.partition)
            self.committed_offsets[key] = message.offset

    def poll_batch(
        self, max_messages: int = 100, timeout: float = 1.0
    ) -> list["MockMessage"]:
        """
        Poll for a batch of messages.

        Args:
            max_messages: Maximum number of messages to return
            timeout: Ignored in mock

        Returns:
            List of MockMessage objects
        """
        results: list[MockMessage] = []
        for _ in range(max_messages):
            msg = self.poll(timeout=timeout)
            if msg is None:
                break
            results.append(msg)
        return results

    def seek(self, partition: Any) -> None:
        """Seek to a specific offset (recorded but not enforced in mock)."""
        pass

    def assignment(self) -> list[Any]:
        """Get the current partition assignment."""
        return list(self._assignment)

    def assign(self, partitions: list[Any]) -> None:
        """Manually assign partitions."""
        self._assignment = list(partitions)

    def position(self, partitions: list[Any]) -> list[Any]:
        """Get current position for partitions (returns input unchanged in mock)."""
        return list(partitions)

    def close(self) -> None:
        """Mark consumer as closed."""
        self._closed = True

    def reset(self) -> None:
        """
        Clear all messages and reset state.

        Examples:
            >>> consumer = MockConsumer()
            >>> consumer.add_message("topic", b"msg")
            >>> consumer.reset()
            >>> assert len(consumer.messages) == 0
        """
        self.messages.clear()
        self.subscribed_topics.clear()
        self.committed_offsets.clear()
        self._closed = False
        self._message_index = 0
        self._assignment.clear()

    def __iter__(self):
        """
        Iterate over queued messages.

        Yields all queued messages then stops. In tests, use poll() in a loop
        or add all messages before iterating.

        Yields:
            MockMessage objects until queue is exhausted
        """
        while True:
            msg = self.poll()
            if msg is None:
                break
            yield msg

    def __enter__(self) -> "MockConsumer":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
