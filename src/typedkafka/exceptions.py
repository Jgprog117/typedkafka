"""Exception classes for typedkafka with clear, actionable error messages."""


class KafkaError(Exception):
    """
    Base exception for all Kafka-related errors.

    All typedkafka exceptions inherit from this base class, making it easy
    to catch all Kafka-related errors with a single except clause.

    Examples:
        >>> try:
        ...     producer.send("topic", "message")
        ... except KafkaError as e:
        ...     logger.error(f"Kafka operation failed: {e}")
    """

    pass


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

    Examples:
        >>> try:
        ...     producer.send("invalid-topic!", {"key": "value"})
        ... except ProducerError as e:
        ...     logger.error(f"Failed to produce message: {e}")
        ...     # Handle retry logic or dead-letter queue
    """

    def __init__(self, message: str, original_error: Exception | None = None):
        """
        Initialize a ProducerError.

        Args:
            message: Human-readable error description
            original_error: The underlying exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


class ConsumerError(KafkaError):
    """
    Raised when a Consumer operation fails.

    This exception is raised when message consumption fails, such as:
    - Message deserialization errors
    - Consumer group coordination failures
    - Offset commit errors
    - Network connectivity issues
    - Invalid consumer configuration

    Attributes:
        message: Human-readable error description
        original_error: The underlying error from confluent-kafka (if any)

    Examples:
        >>> try:
        ...     for message in consumer:
        ...         process(message)
        ... except ConsumerError as e:
        ...     logger.error(f"Consumer error: {e}")
        ...     # Handle reconnection or alerting
    """

    def __init__(self, message: str, original_error: Exception | None = None):
        """
        Initialize a ConsumerError.

        Args:
            message: Human-readable error description
            original_error: The underlying exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


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
        ...     # Log the problematic data for debugging
    """

    def __init__(
        self, message: str, value: object = None, original_error: Exception | None = None
    ):
        """
        Initialize a SerializationError.

        Args:
            message: Human-readable error description
            value: The value that failed to serialize/deserialize
            original_error: The underlying exception that caused this error
        """
        super().__init__(message)
        self.value = value
        self.original_error = original_error
