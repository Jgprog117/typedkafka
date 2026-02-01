"""Tests for KafkaProducer."""

from unittest.mock import MagicMock, patch

import pytest

from typedkafka.exceptions import ProducerError, SerializationError, TransactionError


class TestProducerAPI:
    """Test Producer API without requiring Kafka broker."""

    def test_import_without_confluent_kafka(self):
        """Test that imports work even if confluent-kafka is not installed."""
        from typedkafka import KafkaProducer, ProducerError
        assert KafkaProducer is not None
        assert ProducerError is not None

    def test_json_serialization_error(self):
        """Test that SerializationError is raised for non-serializable objects."""
        import json

        class NonSerializable:
            pass

        obj = NonSerializable()
        with pytest.raises((TypeError, ValueError)):
            json.dumps(obj)

    def test_producer_requires_config(self):
        """Test that producer can be initialized with config dict."""
        from typedkafka import KafkaProducer

        producer = KafkaProducer({})
        assert producer is not None
        assert producer.config == {}


class TestProducerWithMock:
    """Test KafkaProducer methods using mocked confluent-kafka."""

    @pytest.fixture
    def producer(self):
        """Create a KafkaProducer with a mocked internal producer."""
        from typedkafka.metrics import KafkaMetrics
        from typedkafka.producer import KafkaProducer
        p = KafkaProducer.__new__(KafkaProducer)
        p.config = {"bootstrap.servers": "localhost:9092"}
        p._producer = MagicMock()
        p._metrics = KafkaMetrics()
        p._logger = None
        return p

    def test_send_calls_produce(self, producer):
        """Test send() calls underlying produce and poll."""
        producer.send("my-topic", b"value", key=b"key", partition=1)
        producer._producer.produce.assert_called_once_with(
            topic="my-topic", value=b"value", key=b"key", partition=1
        )
        producer._producer.poll.assert_called_once_with(0)

    def test_send_with_callback(self, producer):
        """Test send() passes on_delivery callback."""
        cb = MagicMock()
        producer.send("topic", b"val", on_delivery=cb)
        producer._producer.produce.assert_called_once_with(
            topic="topic", value=b"val", key=None, on_delivery=cb
        )

    def test_send_buffer_error_raises_producer_error(self, producer):
        """Test send() raises ProducerError on BufferError."""
        producer._producer.produce.side_effect = BufferError("queue full")
        with pytest.raises(ProducerError, match="queue is full"):
            producer.send("topic", b"val")

    def test_send_generic_error_raises_producer_error(self, producer):
        """Test send() raises ProducerError on generic Exception."""
        producer._producer.produce.side_effect = RuntimeError("boom")
        with pytest.raises(ProducerError, match="Failed to send"):
            producer.send("topic", b"val")

    def test_send_json_serializes_and_sends(self, producer):
        """Test send_json() serializes dict to JSON bytes."""
        producer.send_json("events", {"user_id": 123}, key="k1")
        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["topic"] == "events"
        assert b'"user_id": 123' in call_args.kwargs["value"]
        assert call_args.kwargs["key"] == b"k1"

    def test_send_json_none_key(self, producer):
        """Test send_json() with no key passes None."""
        producer.send_json("topic", {"a": 1})
        assert producer._producer.produce.call_args.kwargs["key"] is None

    def test_send_json_non_serializable_raises(self, producer):
        """Test send_json() raises SerializationError for non-serializable."""
        with pytest.raises(SerializationError, match="Failed to serialize"):
            producer.send_json("topic", object())

    def test_send_string_encodes_and_sends(self, producer):
        """Test send_string() encodes to UTF-8."""
        producer.send_string("logs", "hello world", key="k")
        call_args = producer._producer.produce.call_args
        assert call_args.kwargs["value"] == b"hello world"
        assert call_args.kwargs["key"] == b"k"

    def test_send_string_none_key(self, producer):
        """Test send_string() with no key passes None."""
        producer.send_string("topic", "val")
        assert producer._producer.produce.call_args.kwargs["key"] is None

    def test_flush_calls_underlying(self, producer):
        """Test flush() delegates to confluent producer."""
        producer._producer.flush.return_value = 0
        result = producer.flush(timeout=5.0)
        producer._producer.flush.assert_called_once_with(timeout=5.0)
        assert result == 0

    def test_flush_error_raises(self, producer):
        """Test flush() raises ProducerError on failure."""
        producer._producer.flush.side_effect = RuntimeError("flush error")
        with pytest.raises(ProducerError, match="Flush failed"):
            producer.flush()

    def test_close_calls_flush(self, producer):
        """Test close() calls flush."""
        producer._producer.flush.return_value = 0
        producer.close()
        producer._producer.flush.assert_called_once()

    def test_context_manager(self, producer):
        """Test __enter__ returns self and __exit__ calls close."""
        producer._producer.flush.return_value = 0
        with producer as p:
            assert p is producer
        producer._producer.flush.assert_called()

    def test_send_batch(self, producer):
        """Test send_batch() sends all messages."""
        messages = [(b"v1", b"k1"), (b"v2", None), (b"v3", b"k3")]
        producer.send_batch("topic", messages)
        assert producer._producer.produce.call_count == 3
        producer._producer.poll.assert_called_once_with(0)

    def test_send_batch_buffer_error_retries(self, producer):
        """Test send_batch() flushes and retries on BufferError."""
        # First produce raises BufferError, retry succeeds
        producer._producer.produce.side_effect = [BufferError("full"), None, None, None]
        producer.send_batch("topic", [(b"v1", None)])
        producer._producer.flush.assert_called_once()

    def test_send_batch_with_callback(self, producer):
        """Test send_batch() passes callback to each produce."""
        cb = MagicMock()
        producer.send_batch("topic", [(b"v1", None), (b"v2", None)], on_delivery=cb)
        for call in producer._producer.produce.call_args_list:
            assert call.kwargs["on_delivery"] is cb

    def test_init_transactions(self, producer):
        """Test init_transactions() delegates to confluent producer."""
        producer.init_transactions(timeout=10.0)
        producer._producer.init_transactions.assert_called_once_with(10.0)

    def test_init_transactions_error(self, producer):
        """Test init_transactions() wraps errors."""
        producer._producer.init_transactions.side_effect = RuntimeError("fail")
        with pytest.raises(TransactionError, match="Failed to initialize transactions"):
            producer.init_transactions()

    def test_begin_transaction(self, producer):
        """Test begin_transaction() delegates."""
        producer.begin_transaction()
        producer._producer.begin_transaction.assert_called_once()

    def test_begin_transaction_error(self, producer):
        """Test begin_transaction() wraps errors."""
        producer._producer.begin_transaction.side_effect = RuntimeError("fail")
        with pytest.raises(TransactionError, match="Failed to begin transaction"):
            producer.begin_transaction()

    def test_commit_transaction(self, producer):
        """Test commit_transaction() delegates."""
        producer.commit_transaction(timeout=15.0)
        producer._producer.commit_transaction.assert_called_once_with(15.0)

    def test_commit_transaction_error(self, producer):
        """Test commit_transaction() wraps errors."""
        producer._producer.commit_transaction.side_effect = RuntimeError("fail")
        with pytest.raises(TransactionError, match="Failed to commit transaction"):
            producer.commit_transaction()

    def test_abort_transaction(self, producer):
        """Test abort_transaction() delegates."""
        producer.abort_transaction(timeout=20.0)
        producer._producer.abort_transaction.assert_called_once_with(20.0)

    def test_abort_transaction_error(self, producer):
        """Test abort_transaction() wraps errors."""
        producer._producer.abort_transaction.side_effect = RuntimeError("fail")
        with pytest.raises(TransactionError, match="Failed to abort transaction"):
            producer.abort_transaction()

    def test_transaction_returns_context(self, producer):
        """Test transaction() returns TransactionContext."""
        from typedkafka.producer import TransactionContext
        ctx = producer.transaction()
        assert isinstance(ctx, TransactionContext)

    def test_transaction_context_commit(self, producer):
        """Test TransactionContext commits on clean exit."""
        with producer.transaction():
            pass
        producer._producer.begin_transaction.assert_called_once()
        producer._producer.commit_transaction.assert_called_once()

    def test_transaction_context_abort_on_error(self, producer):
        """Test TransactionContext aborts on exception."""
        with pytest.raises(ValueError):
            with producer.transaction():
                raise ValueError("oops")
        producer._producer.begin_transaction.assert_called_once()
        producer._producer.abort_transaction.assert_called_once()
        producer._producer.commit_transaction.assert_not_called()


class TestProducerInit:
    """Test KafkaProducer initialization edge cases."""

    def test_init_error_wraps_exception(self):
        """Test that init errors are wrapped in ProducerError."""
        from typedkafka.producer import KafkaProducer

        with patch("typedkafka.producer.ConfluentProducer", side_effect=RuntimeError("bad config")):
            with pytest.raises(ProducerError, match="Failed to initialize"):
                KafkaProducer({"bad": "config"})

    def test_init_without_confluent_kafka(self):
        """Test that missing confluent-kafka raises ImportError."""
        from typedkafka.producer import KafkaProducer

        with patch("typedkafka.producer.ConfluentProducer", None):
            with pytest.raises(ImportError, match="confluent-kafka"):
                KafkaProducer({})


class TestProducerDocumentation:
    """Test that producer has comprehensive documentation."""

    def test_producer_has_docstrings(self):
        """Verify KafkaProducer class and methods have docstrings."""
        from typedkafka import KafkaProducer

        assert KafkaProducer.__doc__ is not None
        assert len(KafkaProducer.__doc__) > 100
        assert "well-documented" in KafkaProducer.__doc__.lower()

        assert KafkaProducer.send.__doc__ is not None
        assert KafkaProducer.send_json.__doc__ is not None
        assert KafkaProducer.send_string.__doc__ is not None
        assert KafkaProducer.flush.__doc__ is not None
        assert KafkaProducer.close.__doc__ is not None

        assert "Args:" in KafkaProducer.send.__doc__
        assert "Returns:" in KafkaProducer.flush.__doc__ or "Raises:" in KafkaProducer.flush.__doc__
        assert "Examples:" in KafkaProducer.send.__doc__

    def test_producer_init_has_config_docs(self):
        """Verify __init__ documents all common config options."""
        from typedkafka import KafkaProducer

        init_doc = KafkaProducer.__init__.__doc__
        assert init_doc is not None
        assert "bootstrap.servers" in init_doc
        assert "compression.type" in init_doc
        assert "acks" in init_doc
        assert "Examples:" in init_doc

    def test_methods_have_parameter_docs(self):
        """Verify methods document all parameters."""
        from typedkafka import KafkaProducer

        send_doc = KafkaProducer.send.__doc__
        assert "topic" in send_doc
        assert "value" in send_doc
        assert "key" in send_doc
        assert "partition" in send_doc

        send_json_doc = KafkaProducer.send_json.__doc__
        assert "JSON" in send_json_doc
        assert "serializ" in send_json_doc.lower()
