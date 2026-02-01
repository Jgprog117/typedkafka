"""
Structured logging for Kafka operations.

Provides optional structured logging that integrates with Python's stdlib
``logging`` module. All logging is opt-in: pass a ``KafkaLogger`` to the
producer or consumer to enable it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogContext:
    """
    Structured context for Kafka log entries.

    Fields that are ``None`` are omitted from log output.

    Attributes:
        topic: Topic name.
        partition: Partition number.
        offset: Message offset.
        key: Message key.
        group_id: Consumer group ID.
        client_id: Client identifier.
        error: Error description.
        extra: Additional key-value pairs.
    """

    topic: str | None = None
    partition: int | None = None
    offset: int | None = None
    key: str | None = None
    group_id: str | None = None
    client_id: str | None = None
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return non-None fields as a dictionary."""
        result: dict[str, Any] = {}
        for name in ("topic", "partition", "offset", "key", "group_id", "client_id", "error"):
            val = getattr(self, name)
            if val is not None:
                result[name] = val
        result.update(self.extra)
        return result


class KafkaLogger:
    """
    Structured logger for Kafka operations.

    Wraps a stdlib ``logging.Logger`` and formats log entries as
    ``event key=value key=value`` strings. When no logger is provided,
    all methods are silent no-ops.

    Args:
        logger: A stdlib logger instance. ``None`` disables logging.
        default_context: Default context merged into every log entry.

    Examples:
        >>> import logging
        >>> kafka_logger = KafkaLogger(logging.getLogger("kafka"))
        >>> producer = KafkaProducer(config, logger=kafka_logger)
        >>> # Sends are now logged automatically
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        default_context: LogContext | None = None,
    ) -> None:
        self._logger = logger
        self._default = default_context or LogContext()

    def _merge(self, ctx: LogContext | None) -> dict[str, Any]:
        """Merge default context with event-specific context."""
        if ctx is None:
            return self._default.to_dict()
        merged = LogContext(
            topic=ctx.topic if ctx.topic is not None else self._default.topic,
            partition=ctx.partition if ctx.partition is not None else self._default.partition,
            offset=ctx.offset if ctx.offset is not None else self._default.offset,
            key=ctx.key if ctx.key is not None else self._default.key,
            group_id=ctx.group_id if ctx.group_id is not None else self._default.group_id,
            client_id=ctx.client_id if ctx.client_id is not None else self._default.client_id,
            error=ctx.error if ctx.error is not None else self._default.error,
            extra={**self._default.extra, **ctx.extra},
        )
        return merged.to_dict()

    def _log(self, level: int, event: str, ctx: LogContext | None = None) -> None:
        if self._logger is None:
            return
        fields = self._merge(ctx)
        parts = " ".join(f"{k}={v}" for k, v in fields.items())
        msg = f"{event} {parts}" if parts else event
        self._logger.log(level, msg)

    def log_send(
        self,
        topic: str,
        key: str | None = None,
        partition: int | None = None,
        **extra: Any,
    ) -> None:
        """Log a producer send event.

        Args:
            topic: Topic name.
            key: Message key.
            partition: Partition number.
            **extra: Additional context fields.
        """
        self._log(logging.INFO, "send", LogContext(topic=topic, key=key, partition=partition, extra=extra))

    def log_poll(
        self,
        topic: str | None = None,
        partition: int | None = None,
        offset: int | None = None,
        **extra: Any,
    ) -> None:
        """Log a consumer poll event.

        Args:
            topic: Topic name.
            partition: Partition number.
            offset: Message offset.
            **extra: Additional context fields.
        """
        self._log(logging.DEBUG, "poll", LogContext(topic=topic, partition=partition, offset=offset, extra=extra))

    def log_commit(
        self,
        topic: str | None = None,
        partition: int | None = None,
        offset: int | None = None,
        **extra: Any,
    ) -> None:
        """Log an offset commit event.

        Args:
            topic: Topic name.
            partition: Partition number.
            offset: Message offset.
            **extra: Additional context fields.
        """
        self._log(logging.INFO, "commit", LogContext(topic=topic, partition=partition, offset=offset, extra=extra))

    def log_error(
        self,
        error: str,
        topic: str | None = None,
        partition: int | None = None,
        **extra: Any,
    ) -> None:
        """Log an error event.

        Args:
            error: Error description.
            topic: Topic name.
            partition: Partition number.
            **extra: Additional context fields.
        """
        self._log(logging.ERROR, "error", LogContext(error=error, topic=topic, partition=partition, extra=extra))

    def log_rebalance(self, event: str, partitions: list[Any] | None = None, **extra: Any) -> None:
        """Log a consumer rebalance event.

        Args:
            event: Rebalance type (assign, revoke, lost).
            partitions: Affected partitions.
            **extra: Additional context fields.
        """
        ctx_extra: dict[str, Any] = {"event": event, **extra}
        if partitions is not None:
            ctx_extra["partitions"] = str(partitions)
        self._log(logging.INFO, "rebalance", LogContext(extra=ctx_extra))

    def log_transaction(self, event: str, **extra: Any) -> None:
        """Log a transaction event.

        Args:
            event: Transaction action (begin, commit, abort).
            **extra: Additional context fields.
        """
        self._log(logging.INFO, "transaction", LogContext(extra={"event": event, **extra}))
