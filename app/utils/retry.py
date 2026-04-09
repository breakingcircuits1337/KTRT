from __future__ import annotations

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class TransientError(Exception):
    """Raised for errors that should trigger a retry (rate limit, 5xx, timeout)."""


def transient_retry(max_attempts: int = 3):
    """Decorator: exponential-backoff retry for transient provider errors."""
    return retry(
        retry=retry_if_exception_type(TransientError),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(max_attempts),
        reraise=True,
    )
