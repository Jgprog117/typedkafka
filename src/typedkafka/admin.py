"""
Kafka Admin Client with comprehensive documentation and full type safety.

Provides a well-documented wrapper for managing Kafka topics, configurations,
and cluster operations.
"""

from typing import Any, Optional

try:
    from confluent_kafka.admin import AdminClient as ConfluentAdminClient
    from confluent_kafka.admin import NewTopic
except ImportError:
    ConfluentAdminClient = None  # type: ignore
    NewTopic = None  # type: ignore

from typedkafka.exceptions import KafkaError


class AdminError(KafkaError):
    """Raised when an admin operation fails."""

    pass


class TopicConfig:
    """
    Configuration for creating a new Kafka topic.

    Examples:
        >>> config = (TopicConfig("my-topic")
        ...     .partitions(3)
        ...     .replication_factor(2)
        ...     .config("retention.ms", "86400000"))  # 1 day retention
    """

    def __init__(self, name: str):
        """
        Initialize topic configuration.

        Args:
            name: Topic name
        """
        self.name = name
        self._num_partitions = 1
        self._replication_factor = 1
        self._config: dict[str, str] = {}

    def partitions(self, count: int) -> "TopicConfig":
        """
        Set number of partitions.

        Args:
            count: Number of partitions (must be >= 1)

        Returns:
            Self for method chaining

        Examples:
            >>> config = TopicConfig("my-topic").partitions(10)
        """
        self._num_partitions = count
        return self

    def replication_factor(self, factor: int) -> "TopicConfig":
        """
        Set replication factor.

        Args:
            factor: Replication factor (typically 2 or 3)

        Returns:
            Self for method chaining

        Examples:
            >>> config = TopicConfig("my-topic").replication_factor(3)
        """
        self._replication_factor = factor
        return self

    def config(self, key: str, value: str) -> "TopicConfig":
        """
        Set a topic configuration parameter.

        Args:
            key: Configuration key (e.g., "retention.ms", "compression.type")
            value: Configuration value

        Returns:
            Self for method chaining

        Examples:
            >>> config = (TopicConfig("logs")
            ...     .config("retention.ms", "604800000")  # 7 days
            ...     .config("compression.type", "gzip"))
        """
        self._config[key] = value
        return self


class KafkaAdmin:
    """
    A well-documented Kafka admin client with full type hints.

    Provides methods for managing topics, configurations, and cluster operations
    with comprehensive documentation and better error messages.

    Examples:
        >>> admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
        >>>
        >>> # Create a topic
        >>> admin.create_topic("events", num_partitions=3, replication_factor=2)
        >>>
        >>> # List all topics
        >>> topics = admin.list_topics()
        >>> print(topics)
        >>>
        >>> # Delete a topic
        >>> admin.delete_topic("old-topic")

    Attributes:
        config: The configuration dictionary used to initialize the admin client
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize a Kafka admin client.

        Args:
            config: Configuration dictionary. Required option:
                - bootstrap.servers (str): Comma-separated broker addresses

        Raises:
            AdminError: If the admin client cannot be initialized

        Examples:
            >>> admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
            >>>
            >>> # With multiple brokers
            >>> admin = KafkaAdmin({
            ...     "bootstrap.servers": "broker1:9092,broker2:9092,broker3:9092"
            ... })
        """
        if ConfluentAdminClient is None:
            raise ImportError(
                "confluent-kafka is required. Install with: pip install confluent-kafka"
            )

        self.config = config
        try:
            self._admin = ConfluentAdminClient(config)
        except Exception as e:
            raise AdminError(f"Failed to initialize Kafka admin client: {e}") from e

    def create_topic(
        self,
        topic: str,
        num_partitions: int = 1,
        replication_factor: int = 1,
        config: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Create a new Kafka topic.

        Args:
            topic: Topic name to create
            num_partitions: Number of partitions (default: 1)
            replication_factor: Replication factor (default: 1, recommended: 2-3)
            config: Optional topic configuration dict
            timeout: Operation timeout in seconds (default: 30.0)

        Raises:
            AdminError: If topic creation fails

        Examples:
            >>> admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
            >>>
            >>> # Simple topic creation
            >>> admin.create_topic("my-topic")
            >>>
            >>> # Topic with multiple partitions and replication
            >>> admin.create_topic("events", num_partitions=10, replication_factor=3)
            >>>
            >>> # Topic with custom configuration
            >>> admin.create_topic(
            ...     "logs",
            ...     num_partitions=5,
            ...     config={"retention.ms": "604800000"}  # 7 days
            ... )
        """
        try:
            new_topic = NewTopic(
                topic,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                config=config or {},
            )

            futures = self._admin.create_topics([new_topic], operation_timeout=timeout)

            # Wait for operation to complete
            for topic_name, future in futures.items():
                try:
                    future.result()  # Block until complete
                except Exception as e:
                    raise AdminError(f"Failed to create topic '{topic_name}': {e}") from e

        except AdminError:
            raise
        except Exception as e:
            raise AdminError(f"Failed to create topic '{topic}': {e}") from e

    def delete_topic(self, topic: str, timeout: float = 30.0) -> None:
        """
        Delete a Kafka topic.

        Args:
            topic: Topic name to delete
            timeout: Operation timeout in seconds (default: 30.0)

        Raises:
            AdminError: If topic deletion fails

        Examples:
            >>> admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
            >>> admin.delete_topic("old-topic")
        """
        try:
            futures = self._admin.delete_topics([topic], operation_timeout=timeout)

            for topic_name, future in futures.items():
                try:
                    future.result()
                except Exception as e:
                    raise AdminError(f"Failed to delete topic '{topic_name}': {e}") from e

        except AdminError:
            raise
        except Exception as e:
            raise AdminError(f"Failed to delete topic '{topic}': {e}") from e

    def list_topics(self, timeout: float = 10.0) -> list[str]:
        """
        List all topics in the Kafka cluster.

        Args:
            timeout: Request timeout in seconds (default: 10.0)

        Returns:
            List of topic names

        Raises:
            AdminError: If listing topics fails

        Examples:
            >>> admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
            >>> topics = admin.list_topics()
            >>> for topic in topics:
            ...     print(f"Topic: {topic}")
        """
        try:
            metadata = self._admin.list_topics(timeout=timeout)
            return list(metadata.topics.keys())
        except Exception as e:
            raise AdminError(f"Failed to list topics: {e}") from e

    def topic_exists(self, topic: str, timeout: float = 10.0) -> bool:
        """
        Check if a topic exists.

        Args:
            topic: Topic name to check
            timeout: Request timeout in seconds (default: 10.0)

        Returns:
            True if topic exists, False otherwise

        Raises:
            AdminError: If the check fails

        Examples:
            >>> admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
            >>> if admin.topic_exists("my-topic"):
            ...     print("Topic exists!")
            ... else:
            ...     admin.create_topic("my-topic")
        """
        try:
            topics = self.list_topics(timeout=timeout)
            return topic in topics
        except Exception as e:
            raise AdminError(f"Failed to check if topic exists: {e}") from e

    def describe_topic(self, topic: str, timeout: float = 10.0) -> dict[str, Any]:
        """
        Get detailed information about a topic.

        Args:
            topic: Topic name
            timeout: Request timeout in seconds (default: 10.0)

        Returns:
            Dict containing topic metadata (partitions, replication, etc.)

        Raises:
            AdminError: If describing the topic fails

        Examples:
            >>> admin = KafkaAdmin({"bootstrap.servers": "localhost:9092"})
            >>> info = admin.describe_topic("my-topic")
            >>> print(f"Partitions: {len(info['partitions'])}")
        """
        try:
            metadata = self._admin.list_topics(topic=topic, timeout=timeout)
            topic_metadata = metadata.topics.get(topic)

            if topic_metadata is None:
                raise AdminError(f"Topic '{topic}' not found")

            return {
                "topic": topic,
                "partitions": [
                    {
                        "id": p.id,
                        "leader": p.leader,
                        "replicas": p.replicas,
                        "isrs": p.isrs,
                    }
                    for p in topic_metadata.partitions.values()
                ],
            }
        except AdminError:
            raise
        except Exception as e:
            raise AdminError(f"Failed to describe topic '{topic}': {e}") from e
