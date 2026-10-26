import pytest

from agentops.validation import validate_premium_result, PremiumValidationError


def test_accepts_reasonable_value():
    assert validate_premium_result(960.0) == 960.0


def test_rejects_negative_value():
    with pytest.raises(PremiumValidationError):
        validate_premium_result(-50.0)


def test_rejects_value_below_minimum():
    with pytest.raises(PremiumValidationError):
        validate_premium_result(0.5)


def test_rejects_absurdly_large_value():
    with pytest.raises(PremiumValidationError):
        validate_premium_result(1_000_000.0)


def test_rejects_nan():
    with pytest.raises(PremiumValidationError):
        validate_premium_result(float("nan"))
