"""Extended tests for aio module to increase coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from typedkafka.aio import MessageBatch, batch_consume
from typedkafka.consumer import KafkaMessage
from typedkafka.exceptions import ProducerError


def _make_raw_msg(value=b"val", key=None, topic="t", partition=0, offset=0):
    msg = MagicMock()
    msg.error.return_value = None
    msg.topic.return_value = topic
    msg.partition.return_value = partition
    msg.offset.return_value = offset
    msg.key.return_value = key
    msg.value.return_value = value
    msg.timestamp.return_value = (0, 0)
    msg.headers.return_value = None
    return msg


class TestAsyncProducerSendString:
    """Test AsyncKafkaProducer.send_string."""

    @pytest.fixture
    def producer(self):
        from concurrent.futures import ThreadPoolExecutor

        from typedkafka.aio import AsyncKafkaProducer

        p = AsyncKafkaProducer.__new__(AsyncKafkaProducer)
        p.config = {}
        p._producer = MagicMock()
        p._executor = ThreadPoolExecutor(max_workers=1)
        p._owns_executor = True
        return p

    @pytest.mark.asyncio
    async def test_send_string(self, producer):
        await producer.send_string("topic", "hello", key="k")
        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["value"] == b"hello"
        assert call_args.kwargs["key"] == b"k"

    @pytest.mark.asyncio
    async def test_send_string_no_key(self, producer):
        await producer.send_string("topic", "hello")
        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["key"] is None

    @pytest.mark.asyncio
    async def test_send_buffer_error(self, producer):
        producer._producer.produce.side_effect = BufferError("full")
        with pytest.raises(ProducerError, match="queue is full"):
            await producer.send("topic", b"data")


class TestMessageBatch:
    """Test MessageBatch class."""

    def test_len(self):
        msgs = [MagicMock(spec=KafkaMessage) for _ in range(3)]
        batch = MessageBatch(msgs)
        assert len(batch) == 3

    def test_iter(self):
        msgs = [MagicMock(spec=KafkaMessage) for _ in range(2)]
        batch = MessageBatch(msgs)
        assert list(batch) == msgs

    def test_topics(self):
        m1 = MagicMock(spec=KafkaMessage)
        m1.topic = "t1"
        m2 = MagicMock(spec=KafkaMessage)
        m2.topic = "t2"
        m3 = MagicMock(spec=KafkaMessage)
        m3.topic = "t1"
        batch = MessageBatch([m1, m2, m3])
        assert batch.topics == {"t1", "t2"}

    def test_empty_batch(self):
        batch = MessageBatch([])
        assert len(batch) == 0
        assert list(batch) == []
        assert batch.topics == set()


class TestBatchConsume:
    """Test batch_consume async generator."""

    @pytest.mark.asyncio
    async def test_batch_by_size(self):
        """Test that batch_consume yields when batch_size is reached."""
        raw_msgs = [_make_raw_msg(value=f"v{i}".encode()) for i in range(5)]

        class FakeConsumer:
            def __init__(self):
                self._msgs = iter(raw_msgs)

            async def __aiter__(self):
                for raw in self._msgs:
                    yield KafkaMessage(raw)

        consumer = FakeConsumer()
        batches = []
        async for batch in batch_consume(consumer, batch_size=2, batch_timeout=999):
            batches.append(batch)

        # 5 messages with batch_size=2 should give 3 batches: 2, 2, 1
        assert len(batches) == 3
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2
        assert len(batches[2]) == 1

    @pytest.mark.asyncio
    async def test_batch_empty_consumer(self):
        """Test batch_consume with no messages."""

        class EmptyConsumer:
            async def __aiter__(self):
                return
                yield

        consumer = EmptyConsumer()
        batches = []
        async for batch in batch_consume(consumer, batch_size=10):
            batches.append(batch)
        assert batches == []
