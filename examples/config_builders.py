"""Type-safe configuration builders with validation, presets, and env loading."""

from typedkafka import ConsumerConfig, KafkaProducer, ProducerConfig

# Fluent builder with validation and IDE autocomplete
config = (
    ProducerConfig()
    .bootstrap_servers("localhost:9092")
    .acks("all")
    .compression("gzip")
    .linger_ms(10)
    .build()
)

producer = KafkaProducer(config)

# Consumer config
consumer_config = (
    ConsumerConfig()
    .bootstrap_servers("localhost:9092")
    .group_id("my-group")
    .auto_offset_reset("earliest")
    .build()
)

# Enable metrics reporting every 5 seconds
metrics_config = (
    ProducerConfig()
    .bootstrap_servers("localhost:9092")
    .stats_interval_ms(5000)
    .build()
)

# Security config (SASL/SSL)
secure_config = (
    ProducerConfig()
    .bootstrap_servers("kafka.example.com:9093")
    .sasl_plain("my-user", "my-password")
    .build()
)

# --- v0.6.0: Configuration presets ---

# High-throughput preset (batching, compression, linger tuned)
ht_config = ProducerConfig.high_throughput("localhost:9092")

# Exactly-once semantics preset (idempotent + transactional)
eo_config = ProducerConfig.exactly_once("localhost:9092", "my-txn-id")

# --- v0.6.0: Environment variable loading (12-factor apps) ---

# Reads KAFKA_BOOTSTRAP_SERVERS, KAFKA_ACKS, etc. from environment
# env_config = ProducerConfig.from_env()
# consumer_env = ConsumerConfig.from_env()

# Custom prefix:
# env_config = ProducerConfig.from_env(prefix="MY_APP_KAFKA_")

# --- v0.6.0: Idempotence and transactional ID in fluent API ---
idempotent_config = (
    ProducerConfig()
    .bootstrap_servers("localhost:9092")
    .enable_idempotence()
    .acks("all")
    .build()
)

txn_config = (
    ProducerConfig()
    .bootstrap_servers("localhost:9092")
    .transactional_id("my-service-txn")
    .build()
)

# --- v0.6.0: Cross-field validation ---
# Validation catches conflicting settings at build time:
# ProducerConfig().bootstrap_servers("localhost:9092").enable_idempotence().acks("1").build(validate=True)
# ^ raises ConfigurationError: idempotence requires acks=all

# Validate required fields at build time
# ConsumerConfig().build(validate=True)  # ConfigurationError: bootstrap.servers is required

# Invalid values raise ValueError immediately:
# ProducerConfig().acks("invalid")       # ValueError
# ProducerConfig().compression("brotli")  # ValueError
