"""OpenTelemetry integration for typedkafka.

Requires: ``pip install opentelemetry-api opentelemetry-sdk``

Provides tracing instrumentation for Kafka producer and consumer operations.
When OpenTelemetry is not installed, all operations gracefully become no-ops.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode

    _OTEL_AVAILABLE = True
except ImportError:
    trace = None  # type: ignore[assignment]
    SpanKind = None  # type: ignore[assignment,misc]
    Status = None  # type: ignore[assignment,misc]
    StatusCode = None  # type: ignore[assignment,misc]
    _OTEL_AVAILABLE = False


class KafkaTracer:
    """OpenTelemetry tracer for Kafka operations.

    If OpenTelemetry is not installed, all span context managers become no-ops.

    Args:
        tracer_name: Name for the OpenTelemetry tracer (default: "typedkafka")

    Examples:
        >>> tracer = KafkaTracer()
        >>> with KafkaProducer(config) as producer:
        ...     with tracer.produce_span("events", key=b"user-123"):
        ...         producer.send_json("events", {"action": "click"})
    """

    def __init__(self, tracer_name: str = "typedkafka") -> None:
        if _OTEL_AVAILABLE:
            self._tracer = trace.get_tracer(tracer_name)
        else:
            self._tracer = None

    @contextmanager
    def produce_span(
        self,
        topic: str,
        key: bytes | None = None,
        partition: int | None = None,
    ) -> Generator[Any, None, None]:
        """Create a span for message production.

        Args:
            topic: Target topic name.
            key: Optional message key.
            partition: Optional partition number.

        Yields:
            The active span, or None if OpenTelemetry is not available.
        """
        if not self._tracer:
            yield None
            return

        with self._tracer.start_as_current_span(
            f"kafka.produce {topic}",
            kind=SpanKind.PRODUCER,
        ) as span:
            span.set_attribute("messaging.system", "kafka")
            span.set_attribute("messaging.destination.name", topic)
            span.set_attribute("messaging.operation", "publish")
            if key:
                span.set_attribute(
                    "messaging.kafka.message.key", key.decode("utf-8", errors="replace")
                )
            if partition is not None:
                span.set_attribute("messaging.kafka.destination.partition", partition)
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @contextmanager
    def consume_span(
        self,
        topic: str,
        partition: int,
        offset: int,
        key: bytes | None = None,
    ) -> Generator[Any, None, None]:
        """Create a span for message consumption.

        Args:
            topic: Source topic name.
            partition: Partition number.
            offset: Message offset.
            key: Optional message key.

        Yields:
            The active span, or None if OpenTelemetry is not available.
        """
        if not self._tracer:
            yield None
            return

        with self._tracer.start_as_current_span(
            f"kafka.consume {topic}",
            kind=SpanKind.CONSUMER,
        ) as span:
            span.set_attribute("messaging.system", "kafka")
            span.set_attribute("messaging.source.name", topic)
            span.set_attribute("messaging.operation", "receive")
            span.set_attribute("messaging.kafka.source.partition", partition)
            span.set_attribute("messaging.kafka.message.offset", offset)
            if key:
                span.set_attribute(
                    "messaging.kafka.message.key", key.decode("utf-8", errors="replace")
                )
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
