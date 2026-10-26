#!/usr/bin/env python
"""Demonstrate the resilience wrapper actually catching a timeout and
retrying past a flaky transient failure -- the "unglamorous parts" the
internship description calls out by name."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentops.execution import execute_with_resilience, TransientError


def flaky_call(call_count: list[int]) -> str:
    call_count[0] += 1
    if call_count[0] < 3:
        raise TransientError(f"simulated transient failure on attempt {call_count[0]}")
    return "succeeded after retries"


def slow_call() -> str:
    time.sleep(5)
    return "never gets here"


def main() -> None:
    print("1. A call that fails twice with a transient error, then succeeds:")
    calls = [0]
    result = execute_with_resilience(flaky_call, calls, max_retries=3, backoff_base_seconds=0.05)
    print(f"   success={result.success} attempts={result.attempts} value={result.value!r}")
    for line in result.attempt_log:
        print(f"     {line}")

    print("\n2. A call that runs longer than its timeout:")
    result = execute_with_resilience(slow_call, timeout_seconds=1.0)
    print(f"   success={result.success} timed_out={result.timed_out} error={result.error!r}")
    for line in result.attempt_log:
        print(f"     {line}")


if __name__ == "__main__":
    main()
