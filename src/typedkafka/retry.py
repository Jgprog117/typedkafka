"""
Retry and backoff utilities for Kafka operations.

Provides decorators and helpers for retrying transient Kafka failures
with configurable backoff strategies.
"""

import functools
import random
import time
from collections.abc import Sequence
from typing import Any, Callable, Optional, TypeVar

from typedkafka.exceptions import KafkaError

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    backoff_base: float = 0.5,
    backoff_max: float = 30.0,
    jitter: bool = True,
    retryable_exceptions: Optional[Sequence[type[BaseException]]] = None,
) -> Callable[[F], F]:
    """
    Decorator that retries a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including the first call).
        backoff_base: Base delay in seconds for exponential backoff.
        backoff_max: Maximum delay in seconds between retries.
        jitter: If True, add random jitter to backoff delay.
        retryable_exceptions: Exception types to retry on.
            Defaults to ``(KafkaError,)`` if not specified.

    Returns:
        Decorated function that retries on failure.

    Raises:
        The last exception if all attempts fail.

    Examples:
        >>> from typedkafka.retry import retry
        >>> from typedkafka.exceptions import ProducerError
        >>>
        >>> @retry(max_attempts=3, backoff_base=1.0)
        ... def send_message(producer, topic, value):
        ...     producer.send(topic, value)
        ...     producer.flush()

        >>> # Retry only specific exceptions
        >>> @retry(max_attempts=5, retryable_exceptions=(ProducerError,))
        ... def produce(producer, data):
        ...     producer.send_json("events", data)
    """
    if retryable_exceptions is None:
        retryable_exceptions = (KafkaError,)

    retry_tuple = tuple(retryable_exceptions)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[BaseException] = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_tuple as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(backoff_base * (2 ** attempt), backoff_max)
                        if jitter:
                            delay = delay * (0.5 + random.random() * 0.5)  # noqa: S311
                        time.sleep(delay)
            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


class RetryPolicy:
    """
    Configurable retry policy for Kafka operations.

    Provides a reusable retry configuration that can be applied to
    multiple operations.

    Examples:
        >>> policy = RetryPolicy(max_attempts=5, backoff_base=1.0)
        >>> result = policy.execute(lambda: producer.send("topic", b"msg"))
    """

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_base: float = 0.5,
        backoff_max: float = 30.0,
        jitter: bool = True,
        retryable_exceptions: Optional[Sequence[type[BaseException]]] = None,
    ):
        """
        Initialize a retry policy.

        Args:
            max_attempts: Maximum number of attempts.
            backoff_base: Base delay in seconds for exponential backoff.
            backoff_max: Maximum delay between retries.
            jitter: If True, add random jitter to delays.
            retryable_exceptions: Exception types to retry on.
                Defaults to ``(KafkaError,)``.
        """
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.jitter = jitter
        self.retryable_exceptions: tuple[type[BaseException], ...] = tuple(
            retryable_exceptions or (KafkaError,)
        )

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: The function to execute.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            The return value of the function.

        Raises:
            The last exception if all attempts fail.

        Examples:
            >>> policy = RetryPolicy(max_attempts=3)
            >>> policy.execute(producer.send, "topic", b"value")
        """
        last_exception: Optional[BaseException] = None
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = min(
                        self.backoff_base * (2 ** attempt), self.backoff_max
                    )
                    if self.jitter:
                        delay = delay * (0.5 + random.random() * 0.5)  # noqa: S311
                    time.sleep(delay)
        raise last_exception  # type: ignore[misc]
