import time

from agentops.execution import execute_with_resilience, TransientError


def test_succeeds_on_first_try():
    result = execute_with_resilience(lambda: 42)
    assert result.success
    assert result.value == 42
    assert result.attempts == 1


def test_retries_past_transient_failures_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("flaky")
        return "ok"

    result = execute_with_resilience(flaky, max_retries=3, backoff_base_seconds=0.01)
    assert result.success
    assert result.value == "ok"
    assert result.attempts == 3


def test_gives_up_after_exhausting_retries():
    def always_fails():
        raise TransientError("never works")

    result = execute_with_resilience(always_fails, max_retries=2, backoff_base_seconds=0.01)
    assert not result.success
    assert result.attempts == 3  # 1 initial try + 2 retries
    assert "retries exhausted" in result.error


def test_non_retryable_exception_fails_immediately():
    def broken():
        raise ValueError("not retryable")

    result = execute_with_resilience(broken, max_retries=5, backoff_base_seconds=0.01)
    assert not result.success
    assert result.attempts == 1
    assert "non-retryable" in result.error


def test_timeout_is_enforced():
    def slow():
        time.sleep(2)
        return "too late"

    result = execute_with_resilience(slow, timeout_seconds=0.2)
    assert not result.success
    assert result.timed_out
    assert "timed out" in result.error


def test_total_seconds_is_tracked():
    result = execute_with_resilience(lambda: time.sleep(0.05))
    assert result.total_seconds >= 0.05
