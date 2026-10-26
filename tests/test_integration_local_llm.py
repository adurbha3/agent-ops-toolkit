"""One true end-to-end test against the real local model, confirming the
full agent (deterministic routing + real RAG generation) actually works,
not just that mocked pieces connect correctly. Skipped if the model cannot
be downloaded in this environment."""
import pytest

from agentops.agent import ClaimsFAQAgent
from agentops.retrieval import Chunk, VectorIndex


@pytest.fixture(scope="module")
def real_llm():
    try:
        from agentops.llm import LocalLLM

        llm = LocalLLM()
        llm.generate("Say hi.", max_new_tokens=5)
        return llm
    except Exception as e:
        pytest.skip(f"local model unavailable in this environment: {e}")


def test_real_agent_answers_a_grounded_lookup_question(real_llm):
    chunks = [Chunk("v::0", "v", "Voltage", "Collision coverage pays for the policyholder's own vehicle after a crash.")]
    agent = ClaimsFAQAgent(index=VectorIndex(chunks), llm=real_llm)
    result = agent.run("What does collision coverage pay for?")
    assert result.succeeded
    assert result.tool_used == "search_policy_docs"
    assert "collision" in result.output.lower() or "vehicle" in result.output.lower()


def test_real_agent_handles_a_calculation(real_llm):
    chunks = [Chunk("v::0", "v", "Voltage", "placeholder")]
    agent = ClaimsFAQAgent(index=VectorIndex(chunks), llm=real_llm)
    result = agent.run("What is 800 times 1.2?")
    assert result.succeeded
    assert result.tool_used == "estimate_premium"
    assert result.output == "960.0"
