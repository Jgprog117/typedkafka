"""Tests for the telemetry module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from typedkafka.telemetry import KafkaTracer


class TestKafkaTracerNoOtel:
    """Tests when OpenTelemetry is not installed."""

    def test_produce_span_noop(self):
        tracer = KafkaTracer()
        tracer._tracer = None
        with tracer.produce_span("topic") as span:
            assert span is None

    def test_consume_span_noop(self):
        tracer = KafkaTracer()
        tracer._tracer = None
        with tracer.consume_span("topic", partition=0, offset=0) as span:
            assert span is None


class TestKafkaTracerWithOtel:
    """Tests when OpenTelemetry is available (mocked)."""

    def _make_tracer_with_mock(self):
        import typedkafka.telemetry as tel_mod

        tracer = KafkaTracer()
        mock_otel_tracer = MagicMock()
        mock_span = MagicMock()
        mock_otel_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
            return_value=mock_span
        )
        mock_otel_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
            return_value=False
        )
        tracer._tracer = mock_otel_tracer
        # Ensure SpanKind, Status, StatusCode are available even without otel
        tel_mod.SpanKind = MagicMock()
        tel_mod.Status = MagicMock()
        tel_mod.StatusCode = MagicMock()
        return tracer, mock_otel_tracer, mock_span

    def test_produce_span_sets_attributes(self):
        tracer, mock_otel_tracer, mock_span = self._make_tracer_with_mock()
        with tracer.produce_span("events", key=b"user-123", partition=2) as span:
            assert span is mock_span
        mock_span.set_attribute.assert_any_call("messaging.system", "kafka")
        mock_span.set_attribute.assert_any_call("messaging.destination.name", "events")
        mock_span.set_attribute.assert_any_call("messaging.operation", "publish")
        mock_span.set_attribute.assert_any_call("messaging.kafka.message.key", "user-123")
        mock_span.set_attribute.assert_any_call("messaging.kafka.destination.partition", 2)

    def test_consume_span_sets_attributes(self):
        tracer, mock_otel_tracer, mock_span = self._make_tracer_with_mock()
        with tracer.consume_span("events", partition=1, offset=42, key=b"k") as span:
            assert span is mock_span
        mock_span.set_attribute.assert_any_call("messaging.system", "kafka")
        mock_span.set_attribute.assert_any_call("messaging.source.name", "events")
        mock_span.set_attribute.assert_any_call("messaging.kafka.source.partition", 1)
        mock_span.set_attribute.assert_any_call("messaging.kafka.message.offset", 42)
        mock_span.set_attribute.assert_any_call("messaging.kafka.message.key", "k")

    def test_produce_span_records_exception(self):
        tracer, mock_otel_tracer, mock_span = self._make_tracer_with_mock()
        with pytest.raises(ValueError, match="boom"):
            with tracer.produce_span("events") as _:
                raise ValueError("boom")
        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()

    def test_consume_span_records_exception(self):
        tracer, mock_otel_tracer, mock_span = self._make_tracer_with_mock()
        with pytest.raises(RuntimeError, match="fail"):
            with tracer.consume_span("events", partition=0, offset=0) as _:
                raise RuntimeError("fail")
        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()
