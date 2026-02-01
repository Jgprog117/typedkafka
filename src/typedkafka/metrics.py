"""
Kafka metrics collection and statistics tracking.

Provides simple counters and parsed statistics from confluent-kafka's
built-in stats_cb callback for monitoring producer and consumer health.
"""

import json as _json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class KafkaStats:
    """Parsed Kafka statistics from confluent-kafka's stats_cb callback.

    This is a subset of the most useful fields from the full statistics JSON.
    Access the complete data via the ``raw`` attribute.

    Attributes:
        name: Client name/id
        client_type: Client type ("producer" or "consumer")
        ts: Timestamp in microseconds since epoch
        time_seconds: Wall clock time in seconds since epoch
        replyq: Number of operations waiting in queue
        msg_cnt: Current number of messages in producer queues
        msg_size: Current total size of messages in producer queues (bytes)
        tx: Total number of requests sent to brokers
        rx: Total number of responses received from brokers
        txbytes: Total number of bytes transmitted to brokers
        rxbytes: Total number of bytes received from brokers
        raw: The full raw statistics dict for advanced use

    Examples:
        >>> stats = KafkaStats.from_json(json_string)
        >>> print(f"Bytes sent: {stats.txbytes}")
        >>> print(f"Messages queued: {stats.msg_cnt}")
    """

    name: str = ""
    client_type: str = ""
    ts: int = 0
    time_seconds: int = 0
    replyq: int = 0
    msg_cnt: int = 0
    msg_size: int = 0
    tx: int = 0
    rx: int = 0
    txbytes: int = 0
    rxbytes: int = 0
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, json_str: str) -> "KafkaStats":
        """Parse a KafkaStats from the JSON string provided by stats_cb.

        Args:
            json_str: JSON string from confluent-kafka's statistics callback.

        Returns:
            Parsed KafkaStats instance.
        """
        data = _json.loads(json_str)
        return cls(
            name=data.get("name", ""),
            client_type=data.get("type", ""),
            ts=data.get("ts", 0),
            time_seconds=data.get("time", 0),
            replyq=data.get("replyq", 0),
            msg_cnt=data.get("msg_cnt", 0),
            msg_size=data.get("msg_size", 0),
            tx=data.get("tx", 0),
            rx=data.get("rx", 0),
            txbytes=data.get("txbytes", 0),
            rxbytes=data.get("rxbytes", 0),
            raw=data,
        )


@dataclass
class KafkaMetrics:
    """Simple counters tracked by the producer or consumer.

    Updated automatically during normal operations (send, poll).
    When statistics reporting is enabled via ``statistics.interval.ms``,
    byte counters and ``last_stats`` are also populated.

    Attributes:
        messages_sent: Total messages successfully queued (producer only)
        messages_received: Total messages received (consumer only)
        errors: Total error count
        bytes_sent: Total bytes transmitted (from stats callback)
        bytes_received: Total bytes received (from stats callback)
        last_stats: Most recent KafkaStats snapshot (None if stats not enabled)

    Examples:
        >>> producer = KafkaProducer(config)
        >>> producer.send("topic", b"hello")
        >>> print(producer.metrics.messages_sent)  # 1
    """

    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    last_stats: Optional[KafkaStats] = None

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.last_stats = None


#: Type alias for user-provided statistics callbacks.
#: Receives a parsed KafkaStats object each time stats are reported.
StatsCallback = Callable[[KafkaStats], None]


def make_stats_cb(
    metrics: KafkaMetrics,
    user_callback: Optional[StatsCallback] = None,
) -> Callable[[str], None]:
    """Create a stats_cb function for confluent-kafka that updates metrics.

    Args:
        metrics: The KafkaMetrics instance to update with byte counters.
        user_callback: Optional user callback that receives parsed KafkaStats.

    Returns:
        A callback suitable for confluent-kafka's ``stats_cb`` config option.

    Examples:
        >>> metrics = KafkaMetrics()
        >>> cb = make_stats_cb(metrics, on_stats=my_handler)
        >>> config["stats_cb"] = cb
    """

    def _stats_cb(json_str: str) -> None:
        stats = KafkaStats.from_json(json_str)
        metrics.bytes_sent = stats.txbytes
        metrics.bytes_received = stats.rxbytes
        metrics.last_stats = stats
        if user_callback is not None:
            user_callback(stats)

    return _stats_cb
