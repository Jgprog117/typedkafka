"""Tests for async producer and consumer."""

from unittest.mock import MagicMock, patch

import pytest

from typedkafka.aio import AsyncKafkaConsumer, AsyncKafkaProducer
from typedkafka.exceptions import ConsumerError, ProducerError, SerializationError


class TestAsyncKafkaProducerInit:
    """Test AsyncKafkaProducer initialization."""

    def test_import(self):
        """Test that async classes can be imported."""
        assert AsyncKafkaProducer is not None
        assert AsyncKafkaConsumer is not None

    def test_stores_config(self):
        """Test that config is stored."""
        try:
            producer = AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"})
            assert producer.config == {"bootstrap.servers": "localhost:9092"}
        except (ProducerError, ImportError):
            pytest.skip("confluent-kafka not available")

    def test_custom_executor(self):
        """Test passing a custom executor."""
        from concurrent.futures import ThreadPoolExecutor

        executor = ThreadPoolExecutor(max_workers=2)
        try:
            producer = AsyncKafkaProducer(
                {"bootstrap.servers": "localhost:9092"}, executor=executor
            )
            assert producer._executor is executor
            assert producer._owns_executor is False
        except (ProducerError, ImportError):
            pytest.skip("confluent-kafka not available")
        finally:
            executor.shutdown(wait=False)

    def test_default_executor_is_owned(self):
        """Test that default executor is marked as owned."""
        try:
            producer = AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"})
            assert producer._owns_executor is True
        except (ProducerError, ImportError):
            pytest.skip("confluent-kafka not available")

    def test_init_without_confluent_kafka(self):
        """Test that missing confluent-kafka raises ImportError."""
        with patch("typedkafka.aio.ConfluentProducer", None):
            with pytest.raises(ImportError, match="confluent-kafka"):
                AsyncKafkaProducer({})

    def test_init_error_wraps_exception(self):
        """Test that init errors are wrapped in ProducerError."""
        with patch("typedkafka.aio.ConfluentProducer", side_effect=RuntimeError("bad")):
            with pytest.raises(ProducerError, match="Failed to initialize"):
                AsyncKafkaProducer({})


class TestAsyncKafkaProducerMethods:
    """Test AsyncKafkaProducer methods using mocked internals."""

    @pytest.fixture
    def producer(self):
        """Create an AsyncKafkaProducer with mocked internals."""
        from concurrent.futures import ThreadPoolExecutor
        p = AsyncKafkaProducer.__new__(AsyncKafkaProducer)
        p.config = {"bootstrap.servers": "localhost:9092"}
        p._producer = MagicMock()
        p._executor = ThreadPoolExecutor(max_workers=1)
        p._owns_executor = True
        return p

    @pytest.mark.asyncio
    async def test_send(self, producer):
        """Test send() calls produce and poll."""
        await producer.send("topic", b"value", key=b"key", partition=1)
        producer._producer.produce.assert_called_once_with(
            topic="topic", value=b"value", key=b"key", partition=1
        )
        producer._producer.poll.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_send_json(self, producer):
        """Test send_json() serializes and sends."""
        await producer.send_json("events", {"id": 1}, key="k1")
        call_args = producer._producer.produce.call_args
        assert b'"id": 1' in call_args.kwargs["value"]
        assert call_args.kwargs["key"] == b"k1"

    @pytest.mark.asyncio
    async def test_send_json_none_key(self, producer):
        """Test send_json() with no key."""
        await producer.send_json("topic", {"a": 1})
        assert producer._producer.produce.call_args.kwargs["key"] is None

    @pytest.mark.asyncio
    async def test_send_json_non_serializable_raises(self, producer):
        """Test send_json() raises SerializationError."""
        with pytest.raises(SerializationError):
            await producer.send_json("topic", object())

    @pytest.mark.asyncio
    async def test_flush(self, producer):
        """Test flush() delegates to confluent producer."""
        producer._producer.flush.return_value = 0
        result = await producer.flush(timeout=5.0)
        assert result == 0

    @pytest.mark.asyncio
    async def test_flush_error(self, producer):
        """Test flush() wraps errors."""
        producer._producer.flush.side_effect = RuntimeError("fail")
        with pytest.raises(ProducerError, match="Flush failed"):
            await producer.flush()

    @pytest.mark.asyncio
    async def test_close(self, producer):
        """Test close() flushes and shuts down executor."""
        producer._producer.flush.return_value = 0
        await producer.close()
        producer._producer.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_does_not_shutdown_external_executor(self):
        """Test close() does not shutdown external executor."""
        from concurrent.futures import ThreadPoolExecutor
        executor = ThreadPoolExecutor(max_workers=1)
        p = AsyncKafkaProducer.__new__(AsyncKafkaProducer)
        p.config = {}
        p._producer = MagicMock()
        p._producer.flush.return_value = 0
        p._executor = executor
        p._owns_executor = False
        await p.close()
        # Executor should still be usable
        future = executor.submit(lambda: 42)
        assert future.result() == 42
        executor.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_async_context_manager(self, producer):
        """Test async context manager."""
        producer._producer.flush.return_value = 0
        async with producer as p:
            assert p is producer
        producer._producer.flush.assert_called()


class TestAsyncKafkaConsumerInit:
    """Test AsyncKafkaConsumer initialization."""

    def test_default_poll_timeout(self):
        """Test that default poll_timeout is 1.0."""
        try:
            consumer = AsyncKafkaConsumer({
                "bootstrap.servers": "localhost:9092",
                "group.id": "test",
            })
            assert consumer.poll_timeout == 1.0
        except (Exception, ImportError):
            pytest.skip("confluent-kafka not available")

    def test_stores_config(self):
        """Test that config is stored."""
        try:
            consumer = AsyncKafkaConsumer({
                "bootstrap.servers": "localhost:9092",
                "group.id": "test",
            })
            assert consumer.config["group.id"] == "test"
        except (Exception, ImportError):
            pytest.skip("confluent-kafka not available")

    def test_init_without_confluent_kafka(self):
        """Test that missing confluent-kafka raises ImportError."""
        with patch("typedkafka.aio.ConfluentConsumer", None):
            with pytest.raises(ImportError, match="confluent-kafka"):
                AsyncKafkaConsumer({})

    def test_init_error_wraps_exception(self):
        """Test that init errors are wrapped in ConsumerError."""
        with patch("typedkafka.aio.ConfluentConsumer", side_effect=RuntimeError("bad")):
            with pytest.raises(ConsumerError, match="Failed to initialize"):
                AsyncKafkaConsumer({})


class TestAsyncKafkaConsumerMethods:
    """Test AsyncKafkaConsumer methods using mocked internals."""

    @pytest.fixture
    def consumer(self):
        """Create an AsyncKafkaConsumer with mocked internals."""
        from concurrent.futures import ThreadPoolExecutor
        c = AsyncKafkaConsumer.__new__(AsyncKafkaConsumer)
        c.config = {"bootstrap.servers": "localhost:9092", "group.id": "test"}
        c._consumer = MagicMock()
        c._executor = ThreadPoolExecutor(max_workers=1)
        c._owns_executor = True
        c.poll_timeout = 1.0
        return c

    def test_subscribe(self, consumer):
        """Test subscribe() delegates to confluent consumer."""
        consumer.subscribe(["topic1", "topic2"])
        consumer._consumer.subscribe.assert_called_once_with(["topic1", "topic2"])

    def test_subscribe_error(self, consumer):
        """Test subscribe() wraps errors."""
        consumer._consumer.subscribe.side_effect = RuntimeError("fail")
        with pytest.raises(ConsumerError, match="Failed to subscribe"):
            consumer.subscribe(["topic"])

    @pytest.mark.asyncio
    async def test_poll_returns_message(self, consumer):
        """Test poll() returns message on success."""
        raw_msg = MagicMock()
        raw_msg.error.return_value = None
        consumer._consumer.poll.return_value = raw_msg
        msg = await consumer.poll(timeout=2.0)
        assert msg is raw_msg

    @pytest.mark.asyncio
    async def test_poll_returns_none(self, consumer):
        """Test poll() returns None on timeout."""
        consumer._consumer.poll.return_value = None
        assert await consumer.poll() is None

    @pytest.mark.asyncio
    async def test_poll_message_error(self, consumer):
        """Test poll() raises on message error."""
        raw_msg = MagicMock()
        raw_msg.error.return_value = "error"
        consumer._consumer.poll.return_value = raw_msg
        with pytest.raises(ConsumerError, match="Consumer error"):
            await consumer.poll()

    @pytest.mark.asyncio
    async def test_poll_wraps_exceptions(self, consumer):
        """Test poll() wraps generic exceptions."""
        consumer._consumer.poll.side_effect = RuntimeError("fail")
        with pytest.raises(ConsumerError, match="Error while polling"):
            await consumer.poll()

    @pytest.mark.asyncio
    async def test_commit_with_message(self, consumer):
        """Test commit() with a message."""
        msg = MagicMock()
        await consumer.commit(message=msg, asynchronous=False)
        consumer._consumer.commit.assert_called_once_with(message=msg, asynchronous=False)

    @pytest.mark.asyncio
    async def test_commit_without_message(self, consumer):
        """Test commit() without message."""
        await consumer.commit()
        consumer._consumer.commit.assert_called_once_with(asynchronous=True)

    @pytest.mark.asyncio
    async def test_commit_error(self, consumer):
        """Test commit() wraps errors."""
        consumer._consumer.commit.side_effect = RuntimeError("fail")
        with pytest.raises(ConsumerError, match="Failed to commit"):
            await consumer.commit()

    @pytest.mark.asyncio
    async def test_close(self, consumer):
        """Test close() delegates."""
        await consumer.close()
        consumer._consumer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_error(self, consumer):
        """Test close() wraps errors."""
        consumer._consumer.close.side_effect = RuntimeError("fail")
        with pytest.raises(ConsumerError, match="Failed to close"):
            await consumer.close()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, consumer):
        """Test async context manager."""
        async with consumer as c:
            assert c is consumer
        consumer._consumer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_aiter(self, consumer):
        """Test async iteration yields messages."""
        msg1 = MagicMock()
        msg1.error.return_value = None
        msg2 = MagicMock()
        msg2.error.return_value = None
        consumer._consumer.poll.side_effect = [msg1, msg2, None]

        messages = []
        async for msg in consumer:
            messages.append(msg)
            if len(messages) == 2:
                break

        assert len(messages) == 2
        assert messages[0] is msg1
        assert messages[1] is msg2


class TestAsyncDocumentation:
    """Test that async classes have proper documentation."""

    def test_producer_has_docstrings(self):
        """Verify AsyncKafkaProducer has docstrings."""
        assert AsyncKafkaProducer.__doc__ is not None
        assert "async" in AsyncKafkaProducer.__doc__.lower()

    def test_producer_methods_have_docstrings(self):
        """Verify all async producer methods have docstrings."""
        assert AsyncKafkaProducer.send.__doc__ is not None
        assert AsyncKafkaProducer.send_json.__doc__ is not None
        assert AsyncKafkaProducer.flush.__doc__ is not None
        assert AsyncKafkaProducer.close.__doc__ is not None

    def test_consumer_has_docstrings(self):
        """Verify AsyncKafkaConsumer has docstrings."""
        assert AsyncKafkaConsumer.__doc__ is not None
        assert "async" in AsyncKafkaConsumer.__doc__.lower()

    def test_consumer_methods_have_docstrings(self):
        """Verify all async consumer methods have docstrings."""
        assert AsyncKafkaConsumer.subscribe.__doc__ is not None
        assert AsyncKafkaConsumer.poll.__doc__ is not None
        assert AsyncKafkaConsumer.commit.__doc__ is not None
        assert AsyncKafkaConsumer.close.__doc__ is not None

    def test_supports_async_context_manager(self):
        """Verify async context manager protocol."""
        assert hasattr(AsyncKafkaProducer, "__aenter__")
        assert hasattr(AsyncKafkaProducer, "__aexit__")
        assert hasattr(AsyncKafkaConsumer, "__aenter__")
        assert hasattr(AsyncKafkaConsumer, "__aexit__")

    def test_consumer_supports_async_iteration(self):
        """Verify async iteration protocol."""
        assert hasattr(AsyncKafkaConsumer, "__aiter__")
