"""Extended tests for exceptions.py to cover __str__ branches."""

from __future__ import annotations

from typedkafka.exceptions import KafkaError, KafkaErrorContext


class TestKafkaErrorStr:
    """Test KafkaError __str__ with various context combinations."""

    def test_str_with_original_error(self):
        err = KafkaError(
            "something failed",
            original_error=ValueError("root cause"),
        )
        s = str(err)
        assert "something failed" in s
        assert "caused_by=ValueError: root cause" in s

    def test_str_with_full_context(self):
        ctx = KafkaErrorContext(topic="events", partition=2, offset=42)
        err = KafkaError("fail", context=ctx)
        s = str(err)
        assert "topic=events" in s
        assert "partition=2" in s
        assert "offset=42" in s

    def test_str_minimal(self):
        err = KafkaError("simple error")
        assert str(err) == "simple error"
