from agentops.agent import ClaimsFAQAgent
from agentops.retrieval import Chunk, VectorIndex
from agentops.llm import StubLLM


def _agent():
    chunks = [Chunk("deductible::0", "deductible", "Deductible", "A deductible is paid out of pocket before insurance covers the rest.")]
    return ClaimsFAQAgent(index=VectorIndex(chunks), llm=StubLLM())


def test_agent_routes_calculation_and_succeeds():
    result = _agent().run("What is 800 times 1.2?")
    assert result.succeeded
    assert result.tool_used == "estimate_premium"
    assert result.output == "960.0"


def test_agent_routes_search_and_succeeds():
    result = _agent().run("How does a deductible work?")
    assert result.succeeded
    assert result.tool_used == "search_policy_docs"
    assert "deductible" in result.output.lower()


def test_agent_reports_failure_for_unnormalizable_calculation():
    result = _agent().run("What does times mean when 5 is involved but no real question exists here?")
    # Contains a math keyword and a digit, so it routes to CALCULATE, but the
    # phrase cannot be normalized to a clean arithmetic expression.
    assert result.tool_used == "estimate_premium"
    assert not result.succeeded
    assert result.error is not None


def test_agent_records_observability_for_every_run():
    agent = _agent()
    agent.run("How does a deductible work?")
    assert len(agent.tracer.spans) == 3  # agent_run, route, execute_tool
    assert agent.metrics.summary()["counters"]["tool.search_policy_docs.successes"] == 1
    assert any(e["event"] == "agent_run_succeeded" for e in agent.logger.events)
