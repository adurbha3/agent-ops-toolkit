#!/usr/bin/env python
"""Run the Claims FAQ agent on a few example questions and print its
trace, metrics, and structured logs -- what an engineer would look at to
see what the agent did, what it cost, and whether it is healthy."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentops.agent import ClaimsFAQAgent
from agentops.llm import LocalLLM
from agentops.retrieval import VectorIndex

EXAMPLE_QUESTIONS = [
    "What does collision coverage pay for?",
    "What is 800 times 1.2?",
    "How does a deductible work?",
    "What is the base rate 600 multiplied by 1.3?",
    "What does an underwriter do?",
]


def main() -> None:
    print("Loading embedding index and local model (first run downloads ~400MB)...")
    index = VectorIndex.from_corpus()
    llm = LocalLLM()
    agent = ClaimsFAQAgent(index=index, llm=llm)

    for question in EXAMPLE_QUESTIONS:
        result = agent.run(question)
        print(f"\nQ: {question}")
        print(f"  Tool: {result.tool_used}  Succeeded: {result.succeeded}")
        if result.succeeded:
            print(f"  A: {result.output}")
        else:
            print(f"  Error: {result.error}")

    print("\n--- Trace (span_id, parent_id, name, duration_seconds) ---")
    for span in agent.tracer.as_tree():
        print(f"  {span['span_id']:>2} parent={span['parent_id']} {span['name']:<14} "
              f"{span['duration_seconds']:.4f}s  {span['attributes']}")

    print("\n--- Metrics ---")
    import json
    print(json.dumps(agent.metrics.summary(), indent=2))

    print("\n--- Error logs ---")
    for event in agent.logger.errors():
        print(f"  {event}")


if __name__ == "__main__":
    main()
