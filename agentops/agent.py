"""The Claims FAQ agent: routes a question to the matching tool, executes it
through the resilience wrapper, and records tracing, metrics, and structured
logs for the whole run.

Routing between the calculator and the document search is handled
deterministically (see routing.py) rather than by asking the local model to
classify the question -- that was tried first and found unreliable (see
routing.py's docstring for the full story of what was tested and why it was
replaced). The local model is used only for what testing showed it does
reliably: generating a grounded answer from retrieved context.
"""
from __future__ import annotations

from dataclasses import dataclass

from agentops.execution import execute_with_resilience, ExecutionResult
from agentops.llm import LLMBackend
from agentops.observability import MetricsRecorder, StructuredLogger, Tracer
from agentops.retrieval import VectorIndex
from agentops.routing import route, ToolChoice
from agentops.tools import estimate_premium, normalize_math_phrase, search_policy_docs, UnsafeExpressionError

TOOL_TIMEOUTS = {ToolChoice.CALCULATE: 2.0, ToolChoice.SEARCH: 15.0}


@dataclass
class AgentRunResult:
    question: str
    succeeded: bool
    tool_used: str | None = None
    output: str | None = None
    error: str | None = None
    attempts: int = 0


class ClaimsFAQAgent:
    def __init__(
        self,
        index: VectorIndex,
        llm: LLMBackend,
        tracer: Tracer | None = None,
        metrics: MetricsRecorder | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.index = index
        self.llm = llm
        self.tracer = tracer or Tracer()
        self.metrics = metrics or MetricsRecorder()
        self.logger = logger or StructuredLogger()

    def run(self, question: str) -> AgentRunResult:
        with self.tracer.span("agent_run", question=question):
            with self.tracer.span("route"):
                tool = route(question)
                self.logger.log("routed", tool=tool.value)

            with self.tracer.span("execute_tool", tool=tool.value):
                if tool == ToolChoice.CALCULATE:
                    result = self._run_calculate(question)
                else:
                    result = execute_with_resilience(
                        search_policy_docs, question, self.index, self.llm,
                        timeout_seconds=TOOL_TIMEOUTS[tool],
                    )

            self.metrics.record_latency(f"tool.{tool.value}", result.total_seconds)

            if not result.success:
                self.metrics.increment(f"tool.{tool.value}.failures")
                self.logger.log(
                    "tool_execution_failed", level="error", tool=tool.value,
                    error=result.error, timed_out=result.timed_out, attempts=result.attempts,
                )
                return AgentRunResult(
                    question=question, succeeded=False, tool_used=tool.value,
                    error=result.error, attempts=result.attempts,
                )

            self.metrics.increment(f"tool.{tool.value}.successes")
            output = str(result.value) if tool == ToolChoice.CALCULATE else result.value["answer"]
            self.logger.log("agent_run_succeeded", tool=tool.value, attempts=result.attempts)

            return AgentRunResult(
                question=question, succeeded=True, tool_used=tool.value,
                output=output, attempts=result.attempts,
            )

    def _run_calculate(self, question: str) -> ExecutionResult:
        try:
            expression = normalize_math_phrase(question)
        except UnsafeExpressionError as e:
            return ExecutionResult(success=False, error=str(e))

        # A bad expression (e.g. one that validate_premium_result rejects) raises
        # inside the worker thread; execute_with_resilience catches it there and
        # reports it as a normal ExecutionResult failure, same as any other tool error.
        return execute_with_resilience(
            estimate_premium, expression, timeout_seconds=TOOL_TIMEOUTS[ToolChoice.CALCULATE]
        )
