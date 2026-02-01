"""
Dead Letter Queue (DLQ) helper for consumer-side error handling.

Routes failed messages to a dead letter topic with error metadata in headers,
enabling reliable error handling without losing messages.
"""

import time
import traceback
from typing import Any, Callable, Optional

from typedkafka.exceptions import ProducerError


class DeadLetterQueue:
    """Routes failed messages to a dead letter topic.

    Wraps an existing producer (KafkaProducer or MockProducer) and sends
    failed messages to a DLQ topic with error metadata in headers.

    Args:
        producer: A KafkaProducer or MockProducer instance used to send DLQ messages.
        topic_fn: Optional callable that maps original topic to DLQ topic name.
            Default: appends ".dlq" to the original topic.
        default_topic: Optional fixed DLQ topic name. If set, all messages go here
            regardless of original topic. Mutually exclusive with topic_fn.

    Raises:
        ValueError: If both topic_fn and default_topic are provided.

    Examples:
        >>> from typedkafka import KafkaProducer
        >>> producer = KafkaProducer({"bootstrap.servers": "localhost:9092"})
        >>> dlq = DeadLetterQueue(producer)
        >>>
        >>> # Route a failed message
        >>> dlq.send(message, error=exc)

        >>> # Custom topic naming
        >>> dlq = DeadLetterQueue(producer, topic_fn=lambda t: f"errors.{t}")

        >>> # Fixed DLQ topic
        >>> dlq = DeadLetterQueue(producer, default_topic="all-errors")
    """

    def __init__(
        self,
        producer: Any,
        topic_fn: Optional[Callable[[str], str]] = None,
        default_topic: Optional[str] = None,
    ) -> None:
        if topic_fn is not None and default_topic is not None:
            raise ValueError("Cannot specify both topic_fn and default_topic")
        self._producer = producer
        self._topic_fn = topic_fn or (lambda t: f"{t}.dlq")
        self._default_topic = default_topic
        self._send_count = 0

    @property
    def send_count(self) -> int:
        """Number of messages sent to the DLQ."""
        return self._send_count

    def send(
        self,
        message: Any,
        error: Optional[Exception] = None,
        extra_headers: Optional[list[tuple[str, bytes]]] = None,
    ) -> None:
        """Send a failed message to the dead letter topic.

        Preserves the original message value and key, and adds error metadata
        as Kafka headers.

        Args:
            message: A KafkaMessage or MockMessage that failed processing.
            error: The exception that caused the failure (optional).
            extra_headers: Additional headers to include.

        Raises:
            ProducerError: If sending to the DLQ topic fails.

        Headers added automatically:
            - dlq.original.topic: Original topic name
            - dlq.original.partition: Original partition number
            - dlq.original.offset: Original message offset
            - dlq.timestamp: Unix timestamp when DLQ send occurred
            - dlq.error.message: Error string (if error provided)
            - dlq.error.type: Error class name (if error provided)
            - dlq.error.traceback: Full traceback (if error provided)
        """
        dlq_topic = self._default_topic or self._topic_fn(message.topic)

        headers: list[tuple[str, bytes]] = [
            ("dlq.original.topic", str(message.topic).encode("utf-8")),
            ("dlq.original.partition", str(message.partition).encode("utf-8")),
            ("dlq.original.offset", str(message.offset).encode("utf-8")),
            ("dlq.timestamp", str(int(time.time())).encode("utf-8")),
        ]

        if error is not None:
            headers.append(("dlq.error.message", str(error).encode("utf-8")))
            headers.append(("dlq.error.type", type(error).__name__.encode("utf-8")))
            tb = traceback.format_exception(type(error), error, error.__traceback__)
            headers.append(("dlq.error.traceback", "".join(tb).encode("utf-8")))

        if extra_headers:
            headers.extend(extra_headers)

        try:
            self._producer.send(
                dlq_topic,
                message.value,
                key=message.key,
                headers=headers,
            )
        except Exception as e:
            raise ProducerError(
                f"Failed to send message to DLQ topic '{dlq_topic}': {e}",
                original_error=e,
            ) from e

        self._send_count += 1


def process_with_dlq(
    message: Any,
    handler: Callable[[Any], None],
    dlq: DeadLetterQueue,
) -> bool:
    """Process a message, routing to DLQ on failure.

    Calls the handler with the message. If the handler raises an exception,
    the message is sent to the dead letter queue with the error details.

    Args:
        message: A KafkaMessage or MockMessage to process.
        handler: Callable that processes the message. Should raise on failure.
        dlq: DeadLetterQueue instance to route failures to.

    Returns:
        True if processing succeeded, False if message was sent to DLQ.

    Examples:
        >>> dlq = DeadLetterQueue(producer)
        >>> for msg in consumer:
        ...     success = process_with_dlq(msg, my_handler, dlq)
        ...     if success:
        ...         consumer.commit(msg)
    """
    try:
        handler(message)
        return True
    except Exception as e:
        dlq.send(message, error=e)
        return False
