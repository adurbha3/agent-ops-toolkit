#!/usr/bin/env python
"""Run the pinned regression suite against the agent and report pass/fail
for each case -- the permanent record of real failures that must not recur."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentops.agent import ClaimsFAQAgent
from agentops.llm import LocalLLM
from agentops.regression import run_suite, SEED_CASES
from agentops.retrieval import VectorIndex


def main() -> None:
    print(f"Loading embedding index and local model, then running {len(SEED_CASES)} regression cases...")
    index = VectorIndex.from_corpus()
    llm = LocalLLM()
    agent = ClaimsFAQAgent(index=index, llm=llm)

    results = run_suite(agent)

    n_passed = sum(1 for r in results if r.passed)
    print(f"\n{n_passed}/{len(results)} regression cases passed.\n")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.case.name}: {r.case.question!r}")
        if not r.passed:
            print(f"         {r.failure_reason}")


if __name__ == "__main__":
    main()
