import pytest

from agentops.tools import estimate_premium, normalize_math_phrase, UnsafeExpressionError
from agentops.validation import PremiumValidationError


def test_estimate_premium_basic_arithmetic():
    assert estimate_premium("800 * 1.2") == 960.0
    assert estimate_premium("2 + 3") == 5


def test_estimate_premium_rejects_name_lookups():
    with pytest.raises(UnsafeExpressionError):
        estimate_premium("__import__('os').system('echo hi')")


def test_estimate_premium_rejects_out_of_range_result():
    with pytest.raises(PremiumValidationError):
        estimate_premium("-50 * 2")


def test_normalize_plain_phrase():
    assert normalize_math_phrase("What is 800 times 1.2?") == "800 * 1.2"


def test_normalize_phrase_with_filler_words():
    # The exact phrasing that broke the first version of this function; see regression.py.
    assert normalize_math_phrase("What is the base rate 600 multiplied by 1.3?") == "600 * 1.3"


def test_normalize_handles_plus_and_minus():
    assert normalize_math_phrase("What is 10 plus 5?") == "10 + 5"
    assert normalize_math_phrase("What is 10 minus 5?") == "10 - 5"


def test_normalize_raises_when_no_number_present():
    with pytest.raises(UnsafeExpressionError):
        normalize_math_phrase("What does collision coverage pay for?")
