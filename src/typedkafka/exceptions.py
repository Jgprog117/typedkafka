"""Exception classes for typedkafka with clear, actionable error messages."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class KafkaErrorContext:
    """Structured context for Kafka errors.

    Provides machine-readable metadata about the Kafka operation that failed,
    making it easier to log, route, or retry errors programmatically.

    Attributes:
        topic: The topic involved in the failed operation
        partition: The partition number
        offset: The message offset
        key: The message key
        timestamp: The message timestamp
        headers: Message headers as a dict
    """

    topic: Optional[str] = None
    partition: Optional[int] = None
    offset: Optional[int] = None
    key: Optional[bytes] = None
    timestamp: Optional[int] = None
    headers: dict[str, bytes] = field(default_factory=dict)


class KafkaError(Exception):
    """
    Base exception for all Kafka-related errors.

    All typedkafka exceptions inherit from this base class, making it easy
    to catch all Kafka-related errors with a single except clause.

    Attributes:
        context: Structured error context with topic/partition/offset metadata
        original_error: The underlying error that caused this exception

    Examples:
        >>> try:
        ...     producer.send("topic", "message")
        ... except KafkaError as e:
        ...     logger.error(f"Kafka operation failed: {e}")
        ...     if e.context.topic:
        ...         logger.error(f"Topic: {e.context.topic}")
    """

    def __init__(
        self,
        message: str,
        context: Optional[KafkaErrorContext] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize a KafkaError.

        Args:
            message: Human-readable error description
            context: Structured context about the failed operation
            original_error: The underlying exception that caused this error
        """
        super().__init__(message)
        self.context = context or KafkaErrorContext()
        self.original_error = original_error

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.context.topic:
            parts.append(f"topic={self.context.topic}")
        if self.context.partition is not None:
            parts.append(f"partition={self.context.partition}")
        if self.context.offset is not None:
            parts.append(f"offset={self.context.offset}")
        if self.original_error:
            parts.append(
                f"caused_by={type(self.original_error).__name__}: {self.original_error}"
            )
        return " | ".join(parts)


class ProducerError(KafkaError):
    """
    Raised when a Producer operation fails.

    This exception is raised when message production fails, such as:
    - Message serialization errors
    - Network connectivity issues
    - Broker unavailability
    - Invalid topic names
    - Queue full errors

    Attributes:
        message: Human-readable error description
        original_error: The underlying error from confluent-kafka (if any)
        context: Structured error context

    Examples:
        >>> try:
        ...     producer.send("invalid-topic!", {"key": "value"})
        ... except ProducerError as e:
        ...     logger.error(f"Failed to produce message: {e}")
    """

    def __init__(
        self,
        message: str,
        context: Optional[KafkaErrorContext] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize a ProducerError.

        Args:
            message: Human-readable error description
            context: Structured error context
            original_error: The underlying exception that caused this error
        """
        super().__init__(message, context=context, original_error=original_error)


class ConsumerError(KafkaError):
    """
    Raised when a Consumer operation fails.

    This exception is raised when message consumption fails, such as:
    - Message deserialization errors
    - Consumer group coordination failures
    - Offset commit errors
    - Network connectivity issues

    Attributes:
        message: Human-readable error description
        original_error: The underlying error from confluent-kafka (if any)
        context: Structured error context

    Examples:
        >>> try:
        ...     for message in consumer:
        ...         process(message)
        ... except ConsumerError as e:
        ...     logger.error(f"Consumer error: {e}")
    """

    def __init__(
        self,
        message: str,
        context: Optional[KafkaErrorContext] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize a ConsumerError.

        Args:
            message: Human-readable error description
            context: Structured error context
            original_error: The underlying exception that caused this error
        """
        super().__init__(message, context=context, original_error=original_error)


class SerializationError(KafkaError):
    """
    Raised when message serialization or deserialization fails.

    This occurs when:
    - JSON encoding/decoding fails
    - Avro schema validation fails
    - Custom serializer raises an exception
    - Message format is invalid

    Attributes:
        message: Human-readable error description
        value: The value that failed to serialize/deserialize
        original_error: The underlying error (if any)

    Examples:
        >>> try:
        ...     producer.send_json("topic", non_serializable_object)
        ... except SerializationError as e:
        ...     logger.error(f"Failed to serialize message: {e}")
    """

    def __init__(
        self,
        message: str,
        value: Any = None,
        context: Optional[KafkaErrorContext] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize a SerializationError.

        Args:
            message: Human-readable error description
            value: The value that failed to serialize/deserialize
            context: Structured error context
            original_error: The underlying exception that caused this error
        """
        super().__init__(message, context=context, original_error=original_error)
        self.value = value


class ConfigurationError(KafkaError):
    """
    Raised when Kafka configuration is invalid.

    This occurs when:
    - Required configuration fields are missing
    - Configuration values are mutually inconsistent
    - Validation of the configuration dictionary fails

    Examples:
        >>> try:
        ...     config = ProducerConfig().build(validate=True)
        ... except ConfigurationError as e:
        ...     logger.error(f"Invalid config: {e}")
    """

    pass


class TransactionError(KafkaError):
    """
    Raised when a transaction operation fails.

    This occurs when:
    - Transaction initialization fails
    - Commit or abort fails
    - The transactional producer enters a fatal state

    Examples:
        >>> try:
        ...     with producer.transaction():
        ...         producer.send("topic", b"msg")
        ... except TransactionError as e:
        ...     logger.error(f"Transaction failed: {e}")
    """

    pass
