"""Validate a tool's output before it reaches the caller -- "unexpected
output" is not only a language-model problem. The deterministic premium
calculator in tools.py can still be handed a nonsensical expression (a
negative base rate, a zero multiplier) that produces a technically-valid but
meaningless number, so its result is checked here before the agent reports
it as a real answer.
"""
from __future__ import annotations

MIN_REASONABLE_PREMIUM = 1.0
MAX_REASONABLE_PREMIUM = 100_000.0


class PremiumValidationError(ValueError):
    pass


def validate_premium_result(value: float) -> float:
    """Raise if a computed premium estimate is outside a plausible range,
    rather than silently returning a nonsensical number (e.g. a negative
    premium from a negative input, or an absurdly large one from a typo)."""
    if value != value:  # NaN check without importing math just for this
        raise PremiumValidationError("premium estimate is not a number (NaN)")
    if value < MIN_REASONABLE_PREMIUM:
        raise PremiumValidationError(
            f"premium estimate {value} is below the minimum plausible value "
            f"({MIN_REASONABLE_PREMIUM}); check the input expression"
        )
    if value > MAX_REASONABLE_PREMIUM:
        raise PremiumValidationError(
            f"premium estimate {value} is above the maximum plausible value "
            f"({MAX_REASONABLE_PREMIUM}); check the input expression"
        )
    return value
