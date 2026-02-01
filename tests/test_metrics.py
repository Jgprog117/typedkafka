"""Tests for metrics collection module."""

import json

from typedkafka.metrics import KafkaMetrics, KafkaStats, make_stats_cb


class TestKafkaStats:
    """Test KafkaStats parsing."""

    def test_from_json_parses_fields(self):
        data = {
            "name": "rdkafka#producer-1",
            "type": "producer",
            "ts": 1000000,
            "time": 1700000000,
            "replyq": 0,
            "msg_cnt": 5,
            "msg_size": 1024,
            "tx": 10,
            "rx": 8,
            "txbytes": 2048,
            "rxbytes": 512,
        }
        stats = KafkaStats.from_json(json.dumps(data))
        assert stats.name == "rdkafka#producer-1"
        assert stats.client_type == "producer"
        assert stats.ts == 1000000
        assert stats.time_seconds == 1700000000
        assert stats.msg_cnt == 5
        assert stats.msg_size == 1024
        assert stats.tx == 10
        assert stats.rx == 8
        assert stats.txbytes == 2048
        assert stats.rxbytes == 512
        assert stats.raw == data

    def test_from_json_defaults_missing_fields(self):
        stats = KafkaStats.from_json("{}")
        assert stats.name == ""
        assert stats.client_type == ""
        assert stats.txbytes == 0

    def test_raw_contains_full_data(self):
        data = {"name": "test", "custom_field": 42}
        stats = KafkaStats.from_json(json.dumps(data))
        assert stats.raw["custom_field"] == 42


class TestKafkaMetrics:
    """Test KafkaMetrics counters."""

    def test_defaults_are_zero(self):
        m = KafkaMetrics()
        assert m.messages_sent == 0
        assert m.messages_received == 0
        assert m.errors == 0
        assert m.bytes_sent == 0
        assert m.bytes_received == 0
        assert m.last_stats is None

    def test_reset_clears_all(self):
        m = KafkaMetrics()
        m.messages_sent = 10
        m.messages_received = 5
        m.errors = 2
        m.bytes_sent = 1000
        m.bytes_received = 500
        m.last_stats = KafkaStats(name="test")

        m.reset()

        assert m.messages_sent == 0
        assert m.messages_received == 0
        assert m.errors == 0
        assert m.bytes_sent == 0
        assert m.bytes_received == 0
        assert m.last_stats is None

    def test_counters_are_mutable(self):
        m = KafkaMetrics()
        m.messages_sent += 1
        m.errors += 3
        assert m.messages_sent == 1
        assert m.errors == 3


class TestMakeStatsCb:
    """Test the stats callback factory."""

    def test_updates_metrics(self):
        metrics = KafkaMetrics()
        cb = make_stats_cb(metrics)
        data = json.dumps({"txbytes": 100, "rxbytes": 50})
        cb(data)
        assert metrics.bytes_sent == 100
        assert metrics.bytes_received == 50
        assert metrics.last_stats is not None
        assert metrics.last_stats.txbytes == 100

    def test_calls_user_callback(self):
        metrics = KafkaMetrics()
        received = []
        cb = make_stats_cb(metrics, user_callback=lambda s: received.append(s))
        cb(json.dumps({"txbytes": 0, "rxbytes": 0}))
        assert len(received) == 1
        assert isinstance(received[0], KafkaStats)

    def test_works_without_user_callback(self):
        metrics = KafkaMetrics()
        cb = make_stats_cb(metrics)
        cb(json.dumps({}))
        assert metrics.last_stats is not None
