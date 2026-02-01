"""Integration tests for structured logging with a real broker."""

from __future__ import annotations

import logging

from tests.integration.conftest import integration


@integration
class TestLoggingIntegration:
    """Test KafkaLogger with real producer/consumer operations."""

    def test_producer_logging(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.logging import KafkaLogger, LogContext

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        test_logger = logging.getLogger("test.producer.logging")
        test_logger.setLevel(logging.DEBUG)
        test_logger.handlers.clear()

        records: list[logging.LogRecord] = []

        class RecordCapture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        test_logger.addHandler(RecordCapture())

        kafka_logger = KafkaLogger(
            test_logger,
            default_context=LogContext(client_id="test-client"),
        )

        try:
            with KafkaProducer(producer_config, logger=kafka_logger) as producer:
                producer.send(unique_topic, b"test message", key=b"key1")
                producer.flush()

            assert len(records) >= 1
            send_msgs = [r for r in records if "send" in r.getMessage()]
            assert len(send_msgs) >= 1
            msg = send_msgs[0].getMessage()
            assert f"topic={unique_topic}" in msg
            assert "client_id=test-client" in msg
        finally:
            admin.delete_topic(unique_topic)

    def test_consumer_logging(self, producer_config, consumer_config, unique_topic):
        from typedkafka import KafkaAdmin, KafkaConsumer, KafkaProducer
        from typedkafka.logging import KafkaLogger, LogContext

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)

        records: list[logging.LogRecord] = []

        class RecordCapture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        test_logger = logging.getLogger("test.consumer.logging")
        test_logger.setLevel(logging.DEBUG)
        test_logger.handlers.clear()
        test_logger.addHandler(RecordCapture())

        kafka_logger = KafkaLogger(
            test_logger,
            default_context=LogContext(group_id="test-group"),
        )

        try:
            with KafkaProducer(producer_config) as producer:
                producer.send_json(unique_topic, {"id": 1})
                producer.flush()

            consumer_config["enable.auto.commit"] = False
            with KafkaConsumer(consumer_config, logger=kafka_logger) as consumer:
                consumer.subscribe([unique_topic])
                msg = None
                for _ in range(10):
                    msg = consumer.poll(timeout=2.0)
                    if msg is not None:
                        break
                assert msg is not None
                consumer.commit(msg, asynchronous=False)

            # Should have poll and commit log entries
            poll_msgs = [r for r in records if "poll" in r.getMessage()]
            commit_msgs = [r for r in records if "commit" in r.getMessage()]
            assert len(poll_msgs) >= 1
            assert len(commit_msgs) >= 1
            assert f"topic={unique_topic}" in commit_msgs[0].getMessage()
        finally:
            admin.delete_topic(unique_topic)

    def test_transaction_logging(self, producer_config, unique_topic):
        import time

        from typedkafka import KafkaAdmin, KafkaProducer
        from typedkafka.logging import KafkaLogger

        producer_config["transactional.id"] = f"test-txn-log-{unique_topic}"
        producer_config["enable.idempotence"] = True
        producer_config["transaction.timeout.ms"] = 60000

        admin = KafkaAdmin(producer_config)
        admin.create_topic(unique_topic, num_partitions=1, replication_factor=1)
        time.sleep(2)

        records: list[logging.LogRecord] = []

        class RecordCapture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        test_logger = logging.getLogger("test.txn.logging")
        test_logger.setLevel(logging.DEBUG)
        test_logger.handlers.clear()
        test_logger.addHandler(RecordCapture())

        kafka_logger = KafkaLogger(test_logger)

        try:
            with KafkaProducer(producer_config, logger=kafka_logger) as producer:
                producer.init_transactions(timeout=60)
                with producer.transaction():
                    producer.send_json(unique_topic, {"txn": True})

            txn_msgs = [r for r in records if "transaction" in r.getMessage()]
            events = [r.getMessage() for r in txn_msgs]
            assert any("event=begin" in e for e in events)
            assert any("event=commit" in e for e in events)
        finally:
            admin.delete_topic(unique_topic)
