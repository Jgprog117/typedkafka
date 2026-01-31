"""Tests for retry utilities."""

import pytest

from typedkafka.exceptions import KafkaError, ProducerError
from typedkafka.retry import RetryPolicy, retry


class TestRetryDecorator:
    """Test the retry decorator."""

    def test_succeeds_first_try(self):
        """Test function that succeeds on first try."""
        call_count = 0

        @retry(max_attempts=3, backoff_base=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeed() == "ok"
        assert call_count == 1

    def test_retries_on_failure(self):
        """Test function retries on KafkaError."""
        call_count = 0

        @retry(max_attempts=3, backoff_base=0.01)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ProducerError("transient failure")
            return "ok"

        assert fail_twice() == "ok"
        assert call_count == 3

    def test_raises_after_max_attempts(self):
        """Test that last exception is raised after all retries fail."""
        @retry(max_attempts=2, backoff_base=0.01)
        def always_fail():
            raise ProducerError("always fails")

        with pytest.raises(ProducerError, match="always fails"):
            always_fail()

    def test_does_not_retry_non_retryable(self):
        """Test that non-retryable exceptions are not retried."""
        call_count = 0

        @retry(max_attempts=3, backoff_base=0.01, retryable_exceptions=(ProducerError,))
        def fail_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            fail_with_value_error()
        assert call_count == 1

    def test_custom_retryable_exceptions(self):
        """Test retry with custom exception types."""
        call_count = 0

        @retry(max_attempts=3, backoff_base=0.01, retryable_exceptions=(ValueError,))
        def fail_with_value():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("retryable")
            return "ok"

        assert fail_with_value() == "ok"
        assert call_count == 3

    def test_no_jitter(self):
        """Test retry without jitter."""
        call_count = 0

        @retry(max_attempts=2, backoff_base=0.01, jitter=False)
        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise KafkaError("fail")
            return "ok"

        assert fail_once() == "ok"
        assert call_count == 2


class TestRetryPolicy:
    """Test RetryPolicy class."""

    def test_execute_succeeds(self):
        """Test execute with successful function."""
        policy = RetryPolicy(max_attempts=3, backoff_base=0.01)
        result = policy.execute(lambda: 42)
        assert result == 42

    def test_execute_retries(self):
        """Test execute retries on failure."""
        call_count = 0
        policy = RetryPolicy(max_attempts=3, backoff_base=0.01)

        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise KafkaError("fail")
            return "ok"

        assert policy.execute(fail_once) == "ok"
        assert call_count == 2

    def test_execute_raises_after_max(self):
        """Test execute raises after max attempts."""
        policy = RetryPolicy(max_attempts=2, backoff_base=0.01)

        with pytest.raises(KafkaError, match="fail"):
            policy.execute(lambda: (_ for _ in ()).throw(KafkaError("fail")))

    def test_execute_with_args(self):
        """Test execute passes args and kwargs."""
        policy = RetryPolicy(max_attempts=1)

        def add(a, b, extra=0):
            return a + b + extra

        assert policy.execute(add, 1, 2, extra=3) == 6

    def test_policy_attributes(self):
        """Test policy stores configuration."""
        policy = RetryPolicy(
            max_attempts=5,
            backoff_base=1.0,
            backoff_max=60.0,
            jitter=False,
            retryable_exceptions=(ValueError,),
        )
        assert policy.max_attempts == 5
        assert policy.backoff_base == 1.0
        assert policy.backoff_max == 60.0
        assert policy.jitter is False
        assert policy.retryable_exceptions == (ValueError,)

    def test_default_retryable_is_kafka_error(self):
        """Test that default retryable exception is KafkaError."""
        policy = RetryPolicy()
        assert policy.retryable_exceptions == (KafkaError,)
