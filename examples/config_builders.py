"""Type-safe configuration builders with validation."""

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

# Validate required fields at build time
# ConsumerConfig().build(validate=True)  # ValueError: bootstrap.servers is required

# Invalid values raise ValueError immediately:
# ProducerConfig().acks("invalid")       # ValueError
# ProducerConfig().compression("brotli")  # ValueError
