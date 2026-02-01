"""Extended tests for producer.py to increase coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from typedkafka.exceptions import ProducerError
from typedkafka.producer import KafkaProducer


class TestProducerInitEdgeCases:
    """Test KafkaProducer init edge cases."""

    def test_init_without_confluent_kafka(self):
        with patch("typedkafka.producer.ConfluentProducer", None):
            with pytest.raises(ImportError, match="confluent-kafka"):
                KafkaProducer({})

    def test_init_with_stats_interval(self):
        mock_producer_cls = MagicMock()
        with patch("typedkafka.producer.ConfluentProducer", mock_producer_cls):
            _ = KafkaProducer({"bootstrap.servers": "localhost:9092", "statistics.interval.ms": 5000})
            # The config passed to ConfluentProducer should have stats_cb injected
            call_config = mock_producer_cls.call_args[0][0]
            assert "stats_cb" in call_config

    def test_init_error(self):
        with patch("typedkafka.producer.ConfluentProducer", side_effect=RuntimeError("fail")):
            with pytest.raises(ProducerError, match="Failed to initialize"):
                KafkaProducer({"bootstrap.servers": "bad"})


class TestProducerSendEdgeCases:
    """Test edge cases in send methods."""

    @pytest.fixture
    def producer(self):
        p = KafkaProducer.__new__(KafkaProducer)
        p.config = {}
        p._producer = MagicMock()
        p._metrics = MagicMock()
        p._metrics.messages_sent = 0
        p._metrics.errors = 0
        p._logger = None
        return p

    def test_send_with_headers(self, producer):
        producer.send("t", b"v", headers=[("h1", b"v1")])
        call_kwargs = producer._producer.produce.call_args.kwargs
        assert call_kwargs["headers"] == [("h1", b"v1")]

    def test_send_general_error(self, producer):
        producer._producer.produce.side_effect = RuntimeError("bad")
        with pytest.raises(ProducerError, match="Failed to send"):
            producer.send("topic", b"value")

    def test_send_batch_buffer_error_then_success(self, producer):
        # First call raises BufferError, flush succeeds, retry succeeds
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise BufferError("full")

        producer._producer.produce.side_effect = side_effect
        producer.send_batch("t", [(b"v1", b"k1")])
        assert call_count[0] == 2
        producer._producer.flush.assert_called_once()

    def test_send_batch_buffer_error_then_error(self, producer):
        producer._producer.produce.side_effect = BufferError("full")
        with pytest.raises(ProducerError, match="after flush"):
            producer.send_batch("t", [(b"v1", b"k1")])

    def test_send_batch_general_error(self, producer):
        producer._producer.produce.side_effect = RuntimeError("fail")
        with pytest.raises(ProducerError, match="Failed to send"):
            producer.send_batch("t", [(b"v1", None)])
