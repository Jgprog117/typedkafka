# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
