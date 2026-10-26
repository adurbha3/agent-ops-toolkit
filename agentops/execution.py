"""A resilient execution wrapper for agent tool/model calls: retries with
exponential backoff on transient failures, and a hard timeout per attempt so
one slow call cannot hang the whole agent -- the "unglamorous parts" of
running an agent in production.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from typing import Any, Callable


class TransientError(Exception):
    """Raised by a call site to signal a retryable failure (a flaky dependency,
    a rate limit, a dropped connection) as opposed to a hard failure."""


@dataclass
class ExecutionResult:
    success: bool
    value: Any = None
    attempts: int = 0
    total_seconds: float = 0.0
    timed_out: bool = False
    error: str | None = None
    attempt_log: list[str] = field(default_factory=list)


def execute_with_resilience(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    backoff_base_seconds: float = 0.05,
    timeout_seconds: float = 5.0,
    **kwargs: Any,
) -> ExecutionResult:
    """Call fn(*args, **kwargs), retrying on TransientError with exponential
    backoff, and enforcing timeout_seconds on every individual attempt."""
    start = time.perf_counter()
    attempt_log: list[str] = []

    for attempt in range(1, max_retries + 2):  # max_retries retries + the first try
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(fn, *args, **kwargs)
            try:
                value = future.result(timeout=timeout_seconds)
                attempt_log.append(f"attempt {attempt}: success")
                return ExecutionResult(
                    success=True, value=value, attempts=attempt,
                    total_seconds=time.perf_counter() - start, attempt_log=attempt_log,
                )
            except FutureTimeoutError:
                attempt_log.append(f"attempt {attempt}: timed out after {timeout_seconds}s")
                return ExecutionResult(
                    success=False, attempts=attempt, total_seconds=time.perf_counter() - start,
                    timed_out=True, error=f"timed out after {timeout_seconds}s",
                    attempt_log=attempt_log,
                )
            except TransientError as e:
                attempt_log.append(f"attempt {attempt}: transient error ({e}), retrying")
                if attempt <= max_retries:
                    time.sleep(backoff_base_seconds * (2 ** (attempt - 1)))
                    continue
                return ExecutionResult(
                    success=False, attempts=attempt, total_seconds=time.perf_counter() - start,
                    error=f"transient error, retries exhausted: {e}", attempt_log=attempt_log,
                )
            except Exception as e:
                attempt_log.append(f"attempt {attempt}: non-retryable error ({e})")
                return ExecutionResult(
                    success=False, attempts=attempt, total_seconds=time.perf_counter() - start,
                    error=f"non-retryable error: {e}", attempt_log=attempt_log,
                )

    # Unreachable, but keeps type checkers happy.
    return ExecutionResult(success=False, attempts=max_retries + 1, error="exhausted retries")
