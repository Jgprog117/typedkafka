"""Tests for structured logging."""

import logging
from unittest.mock import MagicMock

from typedkafka.logging import KafkaLogger, LogContext


class TestLogContext:
    """Test LogContext dataclass."""

    def test_to_dict_empty(self):
        ctx = LogContext()
        assert ctx.to_dict() == {}

    def test_to_dict_with_fields(self):
        ctx = LogContext(topic="events", partition=0, offset=42)
        d = ctx.to_dict()
        assert d == {"topic": "events", "partition": 0, "offset": 42}

    def test_to_dict_skips_none(self):
        ctx = LogContext(topic="events", key=None)
        assert "key" not in ctx.to_dict()

    def test_to_dict_includes_extra(self):
        ctx = LogContext(topic="events", extra={"custom": "value"})
        d = ctx.to_dict()
        assert d["custom"] == "value"


class TestKafkaLogger:
    """Test KafkaLogger."""

    def test_noop_when_no_logger(self):
        kafka_logger = KafkaLogger(logger=None)
        # Should not raise
        kafka_logger.log_send(topic="events")
        kafka_logger.log_poll()
        kafka_logger.log_commit()
        kafka_logger.log_error("something broke")
        kafka_logger.log_rebalance("assign")
        kafka_logger.log_transaction("begin")

    def test_log_send(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(mock_logger)
        kafka_logger.log_send(topic="events", key="user-1")
        mock_logger.log.assert_called_once()
        msg = mock_logger.log.call_args[0][1]
        assert "send" in msg
        assert "topic=events" in msg
        assert "key=user-1" in msg

    def test_log_poll(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(mock_logger)
        kafka_logger.log_poll(topic="events", partition=0, offset=42)
        msg = mock_logger.log.call_args[0][1]
        assert "poll" in msg
        assert "offset=42" in msg

    def test_log_commit(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(mock_logger)
        kafka_logger.log_commit(topic="events", partition=1, offset=100)
        msg = mock_logger.log.call_args[0][1]
        assert "commit" in msg

    def test_log_error(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(mock_logger)
        kafka_logger.log_error("timeout", topic="events")
        level = mock_logger.log.call_args[0][0]
        assert level == logging.ERROR

    def test_log_rebalance(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(mock_logger)
        kafka_logger.log_rebalance("assign", partitions=[0, 1, 2])
        msg = mock_logger.log.call_args[0][1]
        assert "rebalance" in msg
        assert "event=assign" in msg

    def test_log_transaction(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(mock_logger)
        kafka_logger.log_transaction("commit")
        msg = mock_logger.log.call_args[0][1]
        assert "transaction" in msg
        assert "event=commit" in msg

    def test_default_context_merged(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(
            mock_logger,
            default_context=LogContext(client_id="my-app", group_id="my-group"),
        )
        kafka_logger.log_send(topic="events")
        msg = mock_logger.log.call_args[0][1]
        assert "client_id=my-app" in msg
        assert "topic=events" in msg

    def test_event_context_overrides_default(self):
        mock_logger = MagicMock(spec=logging.Logger)
        kafka_logger = KafkaLogger(
            mock_logger,
            default_context=LogContext(topic="default-topic"),
        )
        kafka_logger.log_send(topic="override-topic")
        msg = mock_logger.log.call_args[0][1]
        assert "topic=override-topic" in msg
        assert "default-topic" not in msg
