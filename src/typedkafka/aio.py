"""
Async Kafka producer and consumer wrappers.

Provides asyncio-compatible wrappers around the synchronous KafkaProducer
and KafkaConsumer using a thread pool executor, allowing integration with
async Python applications.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from typedkafka.consumer import KafkaMessage
from typedkafka.exceptions import ConsumerError, ProducerError, SerializationError

try:
    from confluent_kafka import Consumer as ConfluentConsumer
    from confluent_kafka import Producer as ConfluentProducer
except ImportError:
    ConfluentProducer = None  # type: ignore[assignment,misc]
    ConfluentConsumer = None  # type: ignore[assignment,misc]


class AsyncKafkaProducer:
    """
    Async Kafka producer wrapping confluent-kafka with asyncio support.

    Uses a thread pool to run confluent-kafka's synchronous operations
    without blocking the event loop.

    Note:
        This implementation uses a ThreadPoolExecutor to wrap synchronous
        confluent-kafka calls. It does not provide true non-blocking async I/O.
        Each blocking call is offloaded to a thread pool. For high-throughput
        scenarios, consider tuning the executor's max_workers parameter.

    Examples:
        >>> async with AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"}) as producer:
        ...     await producer.send("topic", b"message")
        ...     await producer.flush()

    Attributes:
        config: The configuration dictionary used to initialize the producer
    """

    def __init__(
        self,
        config: dict[str, Any],
        executor: Optional[ThreadPoolExecutor] = None,
    ):
        """
        Initialize an async Kafka producer.

        Args:
            config: Configuration dictionary for the producer.
            executor: Optional ThreadPoolExecutor. If None, a default one is created.

        Raises:
            ProducerError: If the producer cannot be initialized.
        """
        if ConfluentProducer is None:
            raise ImportError(
                "confluent-kafka is required. Install with: pip install confluent-kafka"
            )

        self.config = config
        self._executor = executor or ThreadPoolExecutor(max_workers=1)
        self._owns_executor = executor is None
        try:
            self._producer = ConfluentProducer(config)
        except Exception as e:
            raise ProducerError(
                f"Failed to initialize async Kafka producer: {e}",
                original_error=e,
            ) from e

    async def send(
        self,
        topic: str,
        value: bytes,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
    ) -> None:
        """
        Asynchronously send a message to a Kafka topic.

        Args:
            topic: The topic name to send the message to.
            value: The message payload as bytes.
            key: Optional message key as bytes.
            partition: Optional partition number.

        Raises:
            ProducerError: If the message cannot be queued.
        """
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                self._executor,
                lambda: self._producer.produce(
                    topic=topic, value=value, key=key, partition=partition  # type: ignore[arg-type]
                ),
            )
            await loop.run_in_executor(self._executor, lambda: self._producer.poll(0))
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

    async def send_json(
        self,
        topic: str,
        value: Any,
        key: Optional[str] = None,
        partition: Optional[int] = None,
    ) -> None:
        """
        Asynchronously send a JSON-serialized message.

        Args:
            topic: The topic name.
            value: Any JSON-serializable Python object.
            key: Optional string key.
            partition: Optional partition number.

        Raises:
            SerializationError: If JSON serialization fails.
            ProducerError: If the message cannot be queued.
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
        await self.send(topic, value_bytes, key=key_bytes, partition=partition)

    async def flush(self, timeout: float = -1) -> int:
        """
        Asynchronously wait for all queued messages to be delivered.

        Args:
            timeout: Maximum time to wait in seconds. -1 for infinite.

        Returns:
            Number of messages still in queue.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                self._executor, lambda: self._producer.flush(timeout=timeout)
            )
        except Exception as e:
            raise ProducerError(f"Flush failed: {e}", original_error=e) from e

    async def close(self) -> None:
        """Flush and close the producer."""
        await self.flush()
        if self._owns_executor:
            self._executor.shutdown(wait=False)

    async def __aenter__(self) -> "AsyncKafkaProducer":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class AsyncKafkaConsumer:
    """
    Async Kafka consumer wrapping confluent-kafka with asyncio support.

    Uses a thread pool to run confluent-kafka's synchronous poll without
    blocking the event loop. Supports ``async for`` iteration.

    Note:
        This implementation uses a ThreadPoolExecutor to wrap synchronous
        confluent-kafka calls. It does not provide true non-blocking async I/O.
        Each blocking call is offloaded to a thread pool. For high-throughput
        scenarios, consider tuning the executor's max_workers parameter.

    Examples:
        >>> async with AsyncKafkaConsumer(config) as consumer:
        ...     consumer.subscribe(["topic"])
        ...     async for msg in consumer:
        ...         print(msg.value_as_string())

    Attributes:
        config: The configuration dictionary used to initialize the consumer
    """

    def __init__(
        self,
        config: dict[str, Any],
        executor: Optional[ThreadPoolExecutor] = None,
    ):
        """
        Initialize an async Kafka consumer.

        Args:
            config: Configuration dictionary for the consumer.
            executor: Optional ThreadPoolExecutor.

        Raises:
            ConsumerError: If the consumer cannot be initialized.
        """
        if ConfluentConsumer is None:
            raise ImportError(
                "confluent-kafka is required. Install with: pip install confluent-kafka"
            )

        self.config = config
        self._executor = executor or ThreadPoolExecutor(max_workers=1)
        self._owns_executor = executor is None
        self.poll_timeout: float = 1.0
        try:
            self._consumer = ConfluentConsumer(config)
        except Exception as e:
            raise ConsumerError(
                f"Failed to initialize async Kafka consumer: {e}",
                original_error=e,
            ) from e

    def subscribe(self, topics: list[str], **kwargs: Any) -> None:
        """
        Subscribe to topics.

        Args:
            topics: List of topic names.
            **kwargs: Additional arguments passed to confluent-kafka subscribe.
        """
        try:
            self._consumer.subscribe(topics, **kwargs)
        except Exception as e:
            raise ConsumerError(
                f"Failed to subscribe to topics {topics}: {e}",
                original_error=e,
            ) from e

    async def poll(self, timeout: float = 1.0) -> Optional[KafkaMessage]:
        """
        Asynchronously poll for a single message.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            A KafkaMessage, or None if timeout expired.

        Raises:
            ConsumerError: If an error occurs during polling.
        """
        loop = asyncio.get_event_loop()
        try:
            msg = await loop.run_in_executor(
                self._executor, lambda: self._consumer.poll(timeout=timeout)
            )
            if msg is None:
                return None
            if msg.error():
                raise ConsumerError(f"Consumer error: {msg.error()}")
            return KafkaMessage(msg)
        except ConsumerError:
            raise
        except Exception as e:
            raise ConsumerError(
                f"Error while polling: {e}",
                original_error=e,
            ) from e

    async def commit(self, message: Any = None, asynchronous: bool = True) -> None:
        """
        Asynchronously commit offsets.

        Args:
            message: Specific message to commit. If None, commits all consumed.
            asynchronous: If True, commit asynchronously.
        """
        loop = asyncio.get_event_loop()
        try:
            if message:
                await loop.run_in_executor(
                    self._executor,
                    lambda: self._consumer.commit(message=message, asynchronous=asynchronous),  # type: ignore[call-overload]
                )
            else:
                await loop.run_in_executor(
                    self._executor,
                    lambda: self._consumer.commit(asynchronous=asynchronous),  # type: ignore[call-overload]
                )
        except Exception as e:
            raise ConsumerError(
                f"Failed to commit offsets: {e}",
                original_error=e,
            ) from e

    async def close(self) -> None:
        """Close the consumer and leave the consumer group."""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(self._executor, self._consumer.close)
        except Exception as e:
            raise ConsumerError(
                f"Failed to close consumer: {e}",
                original_error=e,
            ) from e
        if self._owns_executor:
            self._executor.shutdown(wait=False)

    async def __aenter__(self) -> "AsyncKafkaConsumer":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def __aiter__(self) -> AsyncIterator[KafkaMessage]:
        """
        Async iterate over messages indefinitely.

        Yields:
            KafkaMessage objects as they arrive.
        """
        while True:
            msg = await self.poll(timeout=self.poll_timeout)
            if msg is not None:
                yield msg
