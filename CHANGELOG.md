# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Enhanced exceptions**: `KafkaErrorContext` dataclass for structured error metadata; new `ConfigurationError` and `TransactionError` exception classes
- **Configuration presets**: `ProducerConfig.high_throughput()` and `exactly_once()` class methods for common setups
- **Environment config loading**: `ProducerConfig.from_env()` and `ConsumerConfig.from_env()` for 12-factor app config
- `enable_idempotence()` and `transactional_id()` methods on `ProducerConfig`
- Cross-field configuration validation (e.g. idempotence requires `acks=all`)
- **Generic consumer deserialization**: `KafkaMessage.value_as(deserializer)` and `value_deserializer` parameter on `KafkaConsumer`
- **Async improvements**: `AsyncKafkaProducer.send_string()`, `MessageBatch` class, `batch_consume()` async generator
- **Testing enhancements**: `fail_on_topics` on `MockProducer`, `message_count()`, `get_json_messages()`, `MockConsumer.add_string_message()`
- **Integration test infrastructure**: `tests/integration/` with Docker Compose and CI workflow for Kafka broker tests
- **Protobuf serialization**: `ProtobufSerializer`, `ProtobufDeserializer`, `SchemaRegistryProtobufSerializer`, and helper functions in `typedkafka.protobuf`
- **OpenTelemetry tracing**: `KafkaTracer` with `produce_span()` and `consume_span()` context managers following OTel semantic conventions; graceful no-op when OTel is not installed
- `protobuf` and `all` optional dependency groups
- GitHub Pages docs deployment workflow
- Test coverage: 342 tests (up from 320)

## [0.5.0]

### Added
- **Metrics collection**: `KafkaMetrics` and `KafkaStats` dataclasses for tracking throughput, errors, and byte counters on producers and consumers
- `on_stats` callback parameter on `KafkaProducer` and `KafkaConsumer` for receiving parsed statistics from confluent-kafka's `stats_cb`
- `stats_interval_ms()` method on `ProducerConfig` and `ConsumerConfig` builders
- `metrics` property on `KafkaProducer`, `KafkaConsumer`, `MockProducer`, and `MockConsumer`
- **Dead Letter Queue**: `DeadLetterQueue` class for routing failed messages to a DLQ topic with error metadata headers
- `process_with_dlq()` helper for try/except message processing with automatic DLQ routing
- `headers` parameter on `KafkaProducer.send()` and `MockProducer.send()` for attaching Kafka headers to messages
- `MockDeadLetterQueue` in `typedkafka.testing` for unit testing DLQ logic without a broker
- New examples: `examples/metrics.py`, `examples/dead_letter_queue.py`
- Updated examples: headers in `producer.py`, stats/security in `config_builders.py`, metrics and DLQ in `testing_mocks.py`
- Test coverage: 320 tests (up from 294)

## [0.4.0]

### Added
- Consumer offset management: `seek()`, `assignment()`, `assign()`, `position()` methods on `KafkaConsumer`
- `poll_batch()` method on `KafkaConsumer` for consuming multiple messages at once
- Security config helpers: `sasl_plain()`, `sasl_scram()`, `ssl()` on both `ProducerConfig` and `ConsumerConfig`
- Config validation: `build(validate=True)` checks for required fields (`bootstrap.servers`, `group.id`)
- `MockMessage` now matches `KafkaMessage` interface: `value_as_string()`, `value_as_json()`, `key_as_string()`, `__repr__()`
- `MockConsumer` offset management: `seek()`, `assignment()`, `assign()`, `position()`, `poll_batch()`
- `DeliveryCallback` type alias for delivery report callbacks in producer and testing modules
- `KafkaMessage` added to top-level `__all__` exports

### Changed
- Async consumer `poll()` now returns `KafkaMessage` instead of raw confluent-kafka message
- Async consumer `__aiter__` yields `KafkaMessage` objects for API consistency
- Async producer and consumer docstrings now document ThreadPoolExecutor wrapping limitation

### Fixed
- Delivery callback type annotations now compatible with mypy strict checking

## [0.3.3]

### Added
- Separate `CHANGELOG.md` following Keep a Changelog format
- `Makefile` with common dev tasks (`make test`, `make lint`, `make check`, etc.)
- Shared test fixtures in `tests/conftest.py`
- Tests for `admin.py` and `aio.py` (test count: 120 → 146)
- Python 3.13 to CI test matrix
- MkDocs documentation site with Material theme and auto-generated API reference
- `docs` optional dependency group for documentation tooling

### Changed
- Moved inline changelog from README to `CHANGELOG.md`
- Updated documentation URL to GitHub Pages

## [0.3.2]

### Changed
- Move code examples from README into standalone `examples/` directory
- Pin all CI/CD actions to commit SHAs for supply chain security
- Switch PyPI publishing to Trusted Publishers (OIDC) instead of API tokens

### Added
- `py.typed` marker file for PEP 561 compliance

## [0.3.1]

### Changed
- Update README, CONTRIBUTING, and SECURITY docs for v0.3.0 features

## [0.3.0]

### Added
- Transaction support: `init_transactions()`, `begin/commit/abort_transaction()`, `transaction()` context manager
- Async producer and consumer (`typedkafka.aio`)
- Retry utilities: `@retry` decorator and `RetryPolicy` class
- Pluggable serializers: `Serializer`/`Deserializer` ABCs, JSON, String, and Avro implementations
- Batch send: `send_batch()` on producer
- Consumer rebalance callbacks: `on_assign`, `on_revoke`, `on_lost` on `subscribe()`
- Configurable iterator poll timeout via `poll_timeout` attribute
- Config validation: early `ValueError` on invalid `acks`, `compression`, `auto_offset_reset`, `linger_ms`, `batch_size`
- Expanded test suite (120 tests)

## [0.2.0]

### Added
- Testing utilities (MockProducer, MockConsumer)
- Type-safe configuration builders (ProducerConfig, ConsumerConfig)
- Admin client wrapper for topic management

## [0.1.0]

### Added
- Initial release with KafkaProducer, KafkaConsumer, full type hints, context manager support
