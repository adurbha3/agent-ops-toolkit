# AgentOps Toolkit

**A resilience and observability layer for tool-using AI agents: retries, timeouts, output validation, structured tracing and metrics, and a regression-test pipeline that turns real failures into permanent test cases — applied to a small local, no-API-key insurance Claims FAQ agent.**

## Why this exists

This project targets the specific, less glamorous half of building an AI agent: not the agent's first demo, but what it takes to run one in production — handling retries, timeouts, and unexpected model output, adding logging/metrics/tracing, and measuring how well the thing actually works by turning real failures into test cases. Those are deliberately not generic claims; every piece below is built around a failure I actually hit and fixed while building this.

## The debugging story (the actual point of this project)

1. **First design**: ask the local model to output a structured `TOOL: x` / `INPUT: y` reply, with the model transcribing the user's question back as the tool input. Testing showed it would frequently echo one of the few-shot examples' text instead of the real question — confirmed by printing raw model output across several questions.
2. **Simplified design**: stop asking the model to transcribe anything; ask it only to output a single classification label (`CALCULATE` or `SEARCH`), and pass the original question through programmatically. This looked like it worked on an initial test set.
3. **Found it was an illusion**: reordering the exact same two few-shot examples flipped nearly every prediction to match whichever label came first in the prompt. The model was tracking example position, not question content (see `agentops/routing.py`'s docstring for the three prompt variants tested and their raw output).
4. **Final design**: replace the LLM-based routing decision with a small deterministic router (`agentops/routing.py`) for this narrow, two-tool domain, and reserve the local model for what testing actually showed it does reliably — generating a grounded answer from retrieved context.
5. **A second real failure, caught by the agent's own logging**: the deterministic math-phrase parser failed on "What is the base rate 600 multiplied by 1.3?" because it only stripped a fixed list of leading phrases. Diagnosed from the structured error log the agent produced, fixed by reworking the parser to key off the first digit in the text, and pinned as a permanent case in the regression suite (`agentops/regression.py`) so it cannot silently break again.

## Features

- **Resilient execution** (`agentops/execution.py`) — retries with exponential backoff on a `TransientError`, and a hard per-attempt timeout via a thread pool, wrapping any tool or model call in a uniform `ExecutionResult`.
- **Deterministic routing** (`agentops/routing.py`) — routes between the calculator and document search without an unreliable LLM classification step; see the debugging story above for why.
- **Output validation** (`agentops/validation.py`) — a computed premium estimate is checked against a plausible range before being reported as a real answer, rather than trusting a technically-valid but nonsensical number.
- **Observability** (`agentops/observability.py`) — a span-based `Tracer` (parent/child timing for every agent run), a `MetricsRecorder` (counters and latency percentiles per tool), and a `StructuredLogger` (JSON-shaped event log, queryable for errors).
- **Retrieval and generation** (`agentops/retrieval.py`, `agentops/llm.py`, `agentops/tools.py`) — sentence-transformer embeddings over an original insurance-policy knowledge base, answered by a fully local open-source model (`HuggingFaceTB/SmolLM2-360M-Instruct`, no API key) behind a pluggable backend interface.
- **Regression pipeline** (`agentops/regression.py`) — pins real failures (including the base-rate-phrasing bug above) as permanent `RegressionCase`s, re-run on every change.
- **Tested** — 41 automated tests (`pytest`), almost all against the real embedding model or a fast deterministic LLM stub so the suite runs in seconds, plus two true end-to-end integration tests against the real local model — run automatically on push via GitHub Actions.

## Install

```bash
git clone https://github.com/adurbha3/agent-ops-toolkit.git
cd agent-ops-toolkit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Needs Python 3.9+. The first run downloads the embedding model (~90MB) and the local LLM (~360M parameters, ~700MB) from Hugging Face.

## Usage

Run the agent on example questions and see its trace, metrics, and logs:

```bash
python scripts/run_agent.py
```

Run the pinned regression suite:

```bash
python scripts/run_regression.py
```

Watch the resilience wrapper actually catch a retry-then-succeed and a timeout:

```bash
python scripts/simulate_failures.py
```

## Project layout

```
agentops/
  execution.py      retry + timeout wrapper (ExecutionResult, TransientError)
  routing.py         deterministic tool routing (+ the debugging story in its docstring)
  validation.py      output-range validation for the premium calculator
  observability.py   Tracer, MetricsRecorder, StructuredLogger
  retrieval.py       sentence-transformer embeddings + in-memory vector search
  llm.py             pluggable LLM backend: LocalLLM (real) and StubLLM (fast/deterministic)
  tools.py           estimate_premium (safe AST calculator) and search_policy_docs (RAG)
  agent.py           ClaimsFAQAgent: routes, executes, and records observability for a run
  regression.py       RegressionCase / RegressionSuite -- failures pinned as permanent tests
  corpus.py          original insurance-policy knowledge base
scripts/
  run_agent.py        CLI: run example questions, print trace/metrics/logs
  run_regression.py    CLI: run the pinned regression suite
  simulate_failures.py CLI: demonstrate retry and timeout handling directly
tests/                pytest suite covering every module above
```

## Running tests

```bash
pip install -r requirements-dev.txt
pytest -v
```
