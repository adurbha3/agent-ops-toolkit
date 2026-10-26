"""Deterministic routing between the agent's two tools.

This module exists because of a finding from testing, not a design assumed
up front. An earlier version asked the local 360M-parameter model to
classify each question as CALCULATE or SEARCH using a few-shot prompt. Across
several variants it appeared to work, until reordering the exact same two
few-shot examples flipped nearly every prediction to match whichever label
came first in the prompt -- the model was tracking example order, not
question content (confirmed by printing raw output across three prompt
variants with the labels in different positions; see the project README for
the full before/after). Rather than fight that with more prompt tuning, the
routing decision for this narrow, two-tool domain is handled deterministically
here, and the local model is reserved for what it is reliably good at:
generating a grounded answer from retrieved context (see tools.py and the
sibling eng-rag-assistant project's eval results for that).
"""
from __future__ import annotations

import re
from enum import Enum


class ToolChoice(Enum):
    CALCULATE = "estimate_premium"
    SEARCH = "search_policy_docs"


_MATH_KEYWORDS = re.compile(
    r"\b(times|multiplied by|divided by|plus|added to|minus)\b", re.IGNORECASE
)
_HAS_DIGIT = re.compile(r"\d")


def route(question: str) -> ToolChoice:
    """CALCULATE if the question both mentions a math-indicating keyword and
    contains at least one number; SEARCH otherwise (the safe default for
    anything that is not unambiguously a calculation)."""
    if _MATH_KEYWORDS.search(question) and _HAS_DIGIT.search(question):
        return ToolChoice.CALCULATE
    return ToolChoice.SEARCH
