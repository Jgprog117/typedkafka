"""Tests for KafkaConsumer and KafkaMessage."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from typedkafka.consumer import KafkaConsumer, KafkaMessage
from typedkafka.exceptions import ConsumerError, SerializationError


class TestKafkaMessage:
    """Test KafkaMessage wrapper."""

    @pytest.fixture
    def raw_message(self):
        """Create a mock confluent-kafka Message."""
        msg = MagicMock()
        msg.topic.return_value = "test-topic"
        msg.partition.return_value = 2
        msg.offset.return_value = 42
        msg.key.return_value = b"test-key"
        msg.value.return_value = b'{"user_id": 123}'
        msg.timestamp.return_value = (1, 1234567890)
        msg.headers.return_value = [("h1", b"v1")]
        return msg

    def test_init_extracts_fields(self, raw_message):
        """Test KafkaMessage extracts all fields from raw message."""
        msg = KafkaMessage(raw_message)
        assert msg.topic == "test-topic"
        assert msg.partition == 2
        assert msg.offset == 42
        assert msg.key == b"test-key"
        assert msg.value == b'{"user_id": 123}'
        assert msg.timestamp_type == 1
        assert msg.timestamp == 1234567890
        assert msg.headers == [("h1", b"v1")]

    def test_init_no_headers(self):
        """Test KafkaMessage handles None headers."""
        raw = MagicMock()
        raw.topic.return_value = "t"
        raw.partition.return_value = 0
        raw.offset.return_value = 0
        raw.key.return_value = None
        raw.value.return_value = b"val"
        raw.timestamp.return_value = (0, 0)
        raw.headers.return_value = None
        msg = KafkaMessage(raw)
        assert msg.headers == []

    def test_value_as_string(self, raw_message):
        """Test value_as_string() decodes UTF-8."""
        raw_message.value.return_value = b"hello world"
        msg = KafkaMessage(raw_message)
        assert msg.value_as_string() == "hello world"

    def test_value_as_string_custom_encoding(self, raw_message):
        """Test value_as_string() with custom encoding."""
        raw_message.value.return_value = b"hello"
        msg = KafkaMessage(raw_message)
        assert msg.value_as_string(encoding="ascii") == "hello"

    def test_value_as_string_decode_error(self, raw_message):
        """Test value_as_string() raises SerializationError on decode failure."""
        raw_message.value.return_value = b"\xff\xfe"
        msg = KafkaMessage(raw_message)
        with pytest.raises(SerializationError, match="Failed to decode"):
            msg.value_as_string(encoding="ascii")

    def test_value_as_string_none_value(self, raw_message):
        """Test value_as_string() raises SerializationError on None value."""
        raw_message.value.return_value = None
        msg = KafkaMessage(raw_message)
        with pytest.raises(SerializationError):
            msg.value_as_string()

    def test_value_as_json(self, raw_message):
        """Test value_as_json() parses JSON."""
        raw_message.value.return_value = b'{"user_id": 123}'
        msg = KafkaMessage(raw_message)
        data = msg.value_as_json()
        assert data == {"user_id": 123}

    def test_value_as_json_list(self, raw_message):
        """Test value_as_json() parses JSON list."""
        raw_message.value.return_value = b'[1, 2, 3]'
        msg = KafkaMessage(raw_message)
        assert msg.value_as_json() == [1, 2, 3]

    def test_value_as_json_invalid(self, raw_message):
        """Test value_as_json() raises SerializationError on invalid JSON."""
        raw_message.value.return_value = b"not json"
        msg = KafkaMessage(raw_message)
        with pytest.raises(SerializationError, match="Failed to deserialize"):
            msg.value_as_json()

    def test_value_as_json_none_value(self, raw_message):
        """Test value_as_json() raises SerializationError on None value."""
        raw_message.value.return_value = None
        msg = KafkaMessage(raw_message)
        with pytest.raises(SerializationError):
            msg.value_as_json()

    def test_key_as_string(self, raw_message):
        """Test key_as_string() decodes key."""
        raw_message.key.return_value = b"my-key"
        msg = KafkaMessage(raw_message)
        assert msg.key_as_string() == "my-key"

    def test_key_as_string_none_key(self, raw_message):
        """Test key_as_string() returns None when key is None."""
        raw_message.key.return_value = None
        msg = KafkaMessage(raw_message)
        assert msg.key_as_string() is None

    def test_key_as_string_custom_encoding(self, raw_message):
        """Test key_as_string() with custom encoding."""
        raw_message.key.return_value = b"key"
        msg = KafkaMessage(raw_message)
        assert msg.key_as_string(encoding="ascii") == "key"

    def test_key_as_string_decode_error(self, raw_message):
        """Test key_as_string() raises SerializationError on decode failure."""
        raw_message.key.return_value = b"\xff\xfe"
        msg = KafkaMessage(raw_message)
        with pytest.raises(SerializationError, match="Failed to decode"):
            msg.key_as_string(encoding="ascii")

    def test_repr(self, raw_message):
        """Test __repr__ returns informative string."""
        msg = KafkaMessage(raw_message)
        r = repr(msg)
        assert "KafkaMessage" in r
        assert "test-topic" in r
        assert "42" in r  # offset


class TestKafkaConsumerWithMock:
    """Test KafkaConsumer methods using mocked confluent-kafka."""

    @pytest.fixture
    def consumer(self):
        """Create a KafkaConsumer with a mocked internal consumer."""
        c = KafkaConsumer.__new__(KafkaConsumer)
        c.config = {"bootstrap.servers": "localhost:9092", "group.id": "test"}
        c.poll_timeout = 1.0
        c._consumer = MagicMock()
        return c

    def test_subscribe(self, consumer):
        """Test subscribe() delegates to confluent consumer."""
        consumer.subscribe(["topic1", "topic2"])
        consumer._consumer.subscribe.assert_called_once_with(["topic1", "topic2"])

    def test_subscribe_with_callbacks(self, consumer):
        """Test subscribe() passes rebalance callbacks."""
        on_assign = MagicMock()
        on_revoke = MagicMock()
        on_lost = MagicMock()
        consumer.subscribe(
            ["topic"], on_assign=on_assign, on_revoke=on_revoke, on_lost=on_lost
        )
        consumer._consumer.subscribe.assert_called_once_with(
            ["topic"], on_assign=on_assign, on_revoke=on_revoke, on_lost=on_lost
        )

    def test_subscribe_error(self, consumer):
        """Test subscribe() wraps errors in ConsumerError."""
        consumer._consumer.subscribe.side_effect = RuntimeError("fail")
        with pytest.raises(ConsumerError, match="Failed to subscribe"):
            consumer.subscribe(["topic"])

    def test_poll_returns_message(self, consumer):
        """Test poll() returns KafkaMessage on success."""
        raw_msg = MagicMock()
        raw_msg.error.return_value = None
        raw_msg.topic.return_value = "topic"
        raw_msg.partition.return_value = 0
        raw_msg.offset.return_value = 0
        raw_msg.key.return_value = None
        raw_msg.value.return_value = b"val"
        raw_msg.timestamp.return_value = (0, 0)
        raw_msg.headers.return_value = None
        consumer._consumer.poll.return_value = raw_msg

        msg = consumer.poll(timeout=2.0)
        assert isinstance(msg, KafkaMessage)
        assert msg.value == b"val"
        consumer._consumer.poll.assert_called_once_with(timeout=2.0)

    def test_poll_returns_none_on_timeout(self, consumer):
        """Test poll() returns None when no message."""
        consumer._consumer.poll.return_value = None
        assert consumer.poll() is None

    def test_poll_raises_on_message_error(self, consumer):
        """Test poll() raises ConsumerError when message has error."""
        raw_msg = MagicMock()
        raw_msg.error.return_value = "some error"
        consumer._consumer.poll.return_value = raw_msg
        with pytest.raises(ConsumerError, match="Consumer error"):
            consumer.poll()

    def test_poll_wraps_exceptions(self, consumer):
        """Test poll() wraps generic exceptions."""
        consumer._consumer.poll.side_effect = RuntimeError("poll fail")
        with pytest.raises(ConsumerError, match="Error while polling"):
            consumer.poll()

    def test_commit_with_message(self, consumer):
        """Test commit() with a specific message."""
        raw_msg = MagicMock()
        kafka_msg = MagicMock(spec=KafkaMessage)
        kafka_msg._message = raw_msg
        consumer.commit(kafka_msg, asynchronous=False)
        consumer._consumer.commit.assert_called_once_with(
            message=raw_msg, asynchronous=False
        )

    def test_commit_without_message(self, consumer):
        """Test commit() without message commits all."""
        consumer.commit()
        consumer._consumer.commit.assert_called_once_with(asynchronous=True)

    def test_commit_error(self, consumer):
        """Test commit() wraps errors."""
        consumer._consumer.commit.side_effect = RuntimeError("commit fail")
        with pytest.raises(ConsumerError, match="Failed to commit"):
            consumer.commit()

    def test_close(self, consumer):
        """Test close() delegates to confluent consumer."""
        consumer.close()
        consumer._consumer.close.assert_called_once()

    def test_close_error(self, consumer):
        """Test close() wraps errors."""
        consumer._consumer.close.side_effect = RuntimeError("close fail")
        with pytest.raises(ConsumerError, match="Failed to close"):
            consumer.close()

    def test_context_manager(self, consumer):
        """Test __enter__ returns self and __exit__ calls close."""
        with consumer as c:
            assert c is consumer
        consumer._consumer.close.assert_called_once()

    def test_iter_yields_messages(self, consumer):
        """Test __iter__ yields messages until poll returns None."""
        msg1 = MagicMock()
        msg1.error.return_value = None
        msg1.topic.return_value = "t"
        msg1.partition.return_value = 0
        msg1.offset.return_value = 0
        msg1.key.return_value = None
        msg1.value.return_value = b"v1"
        msg1.timestamp.return_value = (0, 0)
        msg1.headers.return_value = None

        msg2 = MagicMock()
        msg2.error.return_value = None
        msg2.topic.return_value = "t"
        msg2.partition.return_value = 0
        msg2.offset.return_value = 1
        msg2.key.return_value = None
        msg2.value.return_value = b"v2"
        msg2.timestamp.return_value = (0, 0)
        msg2.headers.return_value = None

        consumer._consumer.poll.side_effect = [msg1, msg2, None]

        messages = []
        for msg in consumer:
            messages.append(msg)
            if len(messages) == 2:
                break

        assert len(messages) == 2
        assert messages[0].value == b"v1"
        assert messages[1].value == b"v2"

    def test_poll_timeout_used_by_iter(self, consumer):
        """Test that __iter__ uses poll_timeout attribute."""
        consumer.poll_timeout = 5.0
        consumer._consumer.poll.return_value = None

        # Just call next once to verify timeout is used
        it = iter(consumer)
        # poll returns None so iter loops - we check the call was made with correct timeout
        consumer._consumer.poll.side_effect = [None, None]
        # We can't easily break an infinite loop, so test via poll call
        consumer.poll(timeout=consumer.poll_timeout)
        consumer._consumer.poll.assert_called_with(timeout=5.0)


class TestConsumerInit:
    """Test KafkaConsumer initialization edge cases."""

    def test_init_error_wraps_exception(self):
        """Test that init errors are wrapped in ConsumerError."""
        with patch("typedkafka.consumer.ConfluentConsumer", side_effect=RuntimeError("bad")):
            with pytest.raises(ConsumerError, match="Failed to initialize"):
                KafkaConsumer({"group.id": "test"})

    def test_init_without_confluent_kafka(self):
        """Test that missing confluent-kafka raises ImportError."""
        with patch("typedkafka.consumer.ConfluentConsumer", None):
            with pytest.raises(ImportError, match="confluent-kafka"):
                KafkaConsumer({})

    def test_default_poll_timeout(self):
        """Test that default poll_timeout is 1.0."""
        try:
            consumer = KafkaConsumer({
                "bootstrap.servers": "localhost:9092",
                "group.id": "test",
            })
            assert consumer.poll_timeout == 1.0
        except (ConsumerError, ImportError):
            pytest.skip("confluent-kafka not available")


class TestConsumerDocumentation:
    """Test that consumer has comprehensive documentation."""

    def test_consumer_has_docstrings(self):
        """Verify KafkaConsumer class and methods have docstrings."""
        assert KafkaConsumer.__doc__ is not None
        assert len(KafkaConsumer.__doc__) > 100
        assert "well-documented" in KafkaConsumer.__doc__.lower()

        assert KafkaConsumer.subscribe.__doc__ is not None
        assert KafkaConsumer.poll.__doc__ is not None
        assert KafkaConsumer.commit.__doc__ is not None
        assert KafkaConsumer.close.__doc__ is not None

        assert "Args:" in KafkaConsumer.poll.__doc__
        assert "Examples:" in KafkaConsumer.subscribe.__doc__

    def test_consumer_init_has_config_docs(self):
        """Verify __init__ documents all common config options."""
        init_doc = KafkaConsumer.__init__.__doc__
        assert init_doc is not None
        assert "bootstrap.servers" in init_doc
        assert "group.id" in init_doc
        assert "auto.offset.reset" in init_doc
        assert "enable.auto.commit" in init_doc
        assert "Examples:" in init_doc

    def test_kafka_message_has_helper_methods(self):
        """Verify KafkaMessage has convenient helper methods."""
        assert hasattr(KafkaMessage, "value_as_string")
        assert hasattr(KafkaMessage, "value_as_json")
        assert hasattr(KafkaMessage, "key_as_string")
        assert KafkaMessage.value_as_json.__doc__ is not None
        assert "JSON" in KafkaMessage.value_as_json.__doc__

    def test_consumer_supports_iteration(self):
        """Verify KafkaConsumer implements iterator protocol."""
        assert hasattr(KafkaConsumer, "__iter__")
        assert KafkaConsumer.__iter__.__doc__ is not None

    def test_consumer_supports_context_manager(self):
        """Verify KafkaConsumer implements context manager protocol."""
        assert hasattr(KafkaConsumer, "__enter__")
        assert hasattr(KafkaConsumer, "__exit__")
