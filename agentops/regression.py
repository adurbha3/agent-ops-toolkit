"""Turn a real agent failure into a permanent regression test case.

"Help measure how well an existing AI solution works, for example by turning
real failures into test cases, and share what you find with the team" is
implemented literally here: a RegressionCase pins one real input alongside
the behavior it should produce, and a RegressionSuite re-runs every pinned
case so a future change cannot silently reintroduce a fixed bug.

The seed case below is a real failure hit while building this project: the
first version of normalize_math_phrase (tools.py) could not handle "What is
the base rate 600 multiplied by 1.3?" because it only stripped a fixed list
of leading phrases ("what is", "calculate", ...), and this question's filler
text ("the base rate") was not one of them. It was caught by the agent's
error logging (see agent.py/observability.py), diagnosed from that log entry,
fixed by reworking normalize_math_phrase to key off the first digit in the
text instead of a phrase list, and pinned here so the fix cannot regress.
"""
from __future__ import annotations

from dataclasses import dataclass

from agentops.agent import AgentRunResult, ClaimsFAQAgent


@dataclass
class RegressionCase:
    name: str
    question: str
    expect_success: bool
    expected_tool: str | None = None
    expected_output_contains: str | None = None


@dataclass
class RegressionCaseResult:
    case: RegressionCase
    passed: bool
    actual: AgentRunResult
    failure_reason: str | None = None


SEED_CASES: list[RegressionCase] = [
    RegressionCase(
        name="base_rate_phrasing_regression",
        question="What is the base rate 600 multiplied by 1.3?",
        expect_success=True,
        expected_tool="estimate_premium",
        expected_output_contains="780",
    ),
    RegressionCase(
        name="plain_times_phrasing",
        question="What is 800 times 1.2?",
        expect_success=True,
        expected_tool="estimate_premium",
        expected_output_contains="960",
    ),
    RegressionCase(
        name="collision_coverage_lookup",
        question="What does collision coverage pay for?",
        expect_success=True,
        expected_tool="search_policy_docs",
    ),
]


def run_case(agent: ClaimsFAQAgent, case: RegressionCase) -> RegressionCaseResult:
    result = agent.run(case.question)

    if result.succeeded != case.expect_success:
        return RegressionCaseResult(
            case=case, passed=False, actual=result,
            failure_reason=f"expected succeeded={case.expect_success}, got {result.succeeded}",
        )
    if case.expected_tool is not None and result.tool_used != case.expected_tool:
        return RegressionCaseResult(
            case=case, passed=False, actual=result,
            failure_reason=f"expected tool {case.expected_tool!r}, got {result.tool_used!r}",
        )
    if case.expected_output_contains is not None:
        output = result.output or ""
        if case.expected_output_contains not in output:
            return RegressionCaseResult(
                case=case, passed=False, actual=result,
                failure_reason=f"expected output to contain {case.expected_output_contains!r}, got {output!r}",
            )
    return RegressionCaseResult(case=case, passed=True, actual=result)


def run_suite(agent: ClaimsFAQAgent, cases: list[RegressionCase] = SEED_CASES) -> list[RegressionCaseResult]:
    return [run_case(agent, case) for case in cases]
