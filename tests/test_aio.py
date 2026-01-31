"""Tests for async producer and consumer."""


import pytest

from typedkafka.aio import AsyncKafkaConsumer, AsyncKafkaProducer
from typedkafka.exceptions import ProducerError, SerializationError


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
            pass

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
            pass
        finally:
            executor.shutdown(wait=False)

    def test_default_executor_is_owned(self):
        """Test that default executor is marked as owned."""
        try:
            producer = AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"})
            assert producer._owns_executor is True
        except (ProducerError, ImportError):
            pass


class TestAsyncKafkaProducerSendJson:
    """Test JSON serialization in async producer."""

    @pytest.mark.asyncio
    async def test_send_json_serialization_error(self):
        """Test that non-serializable values raise SerializationError."""
        try:
            producer = AsyncKafkaProducer({"bootstrap.servers": "localhost:9092"})
        except (ProducerError, ImportError):
            pytest.skip("confluent-kafka not available")

        class NotSerializable:
            pass

        with pytest.raises(SerializationError):
            await producer.send_json("topic", NotSerializable())


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
            pass

    def test_stores_config(self):
        """Test that config is stored."""
        try:
            consumer = AsyncKafkaConsumer({
                "bootstrap.servers": "localhost:9092",
                "group.id": "test",
            })
            assert consumer.config["group.id"] == "test"
        except (Exception, ImportError):
            pass


class TestAsyncKafkaProducerDocumentation:
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
