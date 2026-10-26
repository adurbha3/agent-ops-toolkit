"""A pluggable LLM backend: a real local open-source model for actual use,
and a fast deterministic stub for unit tests."""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

LOCAL_MODEL_NAME = "HuggingFaceTB/SmolLM2-360M-Instruct"


class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_new_tokens: int = 80) -> str:
        """Return a generated response to a single-turn prompt."""


@lru_cache(maxsize=1)
def _load_local_pipeline():
    from transformers import pipeline

    return pipeline("text-generation", model=LOCAL_MODEL_NAME)


class LocalLLM(LLMBackend):
    def generate(self, prompt: str, max_new_tokens: int = 80) -> str:
        pipe = _load_local_pipeline()
        messages = [{"role": "user", "content": prompt}]
        output = pipe(messages, max_new_tokens=max_new_tokens, do_sample=False)
        return output[0]["generated_text"][-1]["content"].strip()


class StubLLM(LLMBackend):
    """A fast, scriptable backend for tests: returns a pre-programmed sequence
    of responses (or echoes context) instead of running a model."""

    def __init__(self, scripted_responses: list[str] | None = None):
        self._scripted = list(scripted_responses) if scripted_responses else None
        self._call_count = 0

    def generate(self, prompt: str, max_new_tokens: int = 80) -> str:
        self._call_count += 1
        if self._scripted is not None:
            index = min(self._call_count - 1, len(self._scripted) - 1)
            return self._scripted[index]
        if "Context:" in prompt:
            context = prompt.split("Context:", 1)[1].split("Question:")[0].strip()
            first_sentence = context.split(".")[0].strip()
            return first_sentence + "." if first_sentence else "I do not know."
        return "I do not know."
