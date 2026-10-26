from agentops.agent import ClaimsFAQAgent
from agentops.llm import StubLLM
from agentops.regression import run_suite, RegressionCase
from agentops.retrieval import Chunk, VectorIndex


def _agent():
    chunks = [Chunk("collision::0", "collision", "Collision", "Collision coverage pays for the policyholder's own vehicle after a crash.")]
    return ClaimsFAQAgent(index=VectorIndex(chunks), llm=StubLLM())


def test_seed_cases_all_pass_against_the_current_agent():
    """The three pinned cases, including the real base-rate-phrasing bug this
    project hit, must stay fixed."""
    results = run_suite(_agent())
    failures = [r for r in results if not r.passed]
    assert not failures, [f"{r.case.name}: {r.failure_reason}" for r in failures]


def test_run_suite_detects_a_genuine_regression():
    """If a case's expectation no longer matches reality, the suite must say so."""
    case = RegressionCase(
        name="impossible_expectation",
        question="What is 800 times 1.2?",
        expect_success=True,
        expected_output_contains="this number will never appear",
    )
    results = run_suite(_agent(), cases=[case])
    assert not results[0].passed
    assert "this number will never appear" in results[0].failure_reason
