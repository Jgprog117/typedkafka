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

# Invalid values raise ValueError immediately:
# ProducerConfig().acks("invalid")       # ValueError
# ProducerConfig().compression("brotli")  # ValueError
