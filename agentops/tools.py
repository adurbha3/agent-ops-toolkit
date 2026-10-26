"""The Claims FAQ agent's two tools: a RAG-backed policy document search, and
a safe premium-estimate calculator."""
from __future__ import annotations

import ast
import operator
import re

from agentops.llm import LLMBackend
from agentops.retrieval import VectorIndex
from agentops.validation import validate_premium_result

_ALLOWED_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
}

RAG_PROMPT_TEMPLATE = (
    "Answer the question using only the information in the context below. "
    "If the context does not contain the answer, say you do not know. "
    "Keep the answer to one or two sentences.\n\n"
    "Context: {context}\n\n"
    "Question: {question}\n"
    "Answer:"
)


class UnsafeExpressionError(ValueError):
    pass


_WORD_TO_OPERATOR = [
    (re.compile(r"\bmultiplied by\b", re.IGNORECASE), "*"),
    (re.compile(r"\btimes\b", re.IGNORECASE), "*"),
    (re.compile(r"\bdivided by\b", re.IGNORECASE), "/"),
    (re.compile(r"\bplus\b", re.IGNORECASE), "+"),
    (re.compile(r"\badded to\b", re.IGNORECASE), "+"),
    (re.compile(r"\bminus\b", re.IGNORECASE), "-"),
]
_NUMERIC_EXPRESSION = re.compile(r"^[\d\s+\-*/().]+$")
_FIRST_DIGIT = re.compile(r"\d")


def normalize_math_phrase(question: str) -> str:
    """Turn a natural-language premium question into a plain arithmetic
    expression deterministically, e.g. "What is 800 times 1.2?" -> "800 * 1.2",
    or "What is the base rate 600 multiplied by 1.3?" -> "600 * 1.3".

    This is handled with regex rather than asking the model to transcribe
    the expression, because a small local model proved unreliable at
    accurately retyping numbers it was shown (see routing.py's docstring for
    the related finding) -- a deterministic parser is the right tool for a
    narrow, well-defined pattern like this one.

    Rather than stripping a fixed list of leading phrases (which missed real
    phrasings like "What is the base rate 600 multiplied by 1.3?" during
    testing -- see tests/test_regression.py for that exact case), this finds
    the first digit in the text and keeps everything from there onward, since
    a premium question always leads with filler words and ends with the
    actual expression.
    """
    text = question.strip().rstrip("?").strip()
    match = _FIRST_DIGIT.search(text)
    if not match:
        raise UnsafeExpressionError(f"found no number in the question: {question!r}")
    text = text[match.start():]
    for pattern, replacement in _WORD_TO_OPERATOR:
        text = pattern.sub(replacement, text)
    text = re.sub(r"\s+", " ", text).strip()
    if not _NUMERIC_EXPRESSION.match(text):
        raise UnsafeExpressionError(f"could not normalize to a plain arithmetic expression: {question!r}")
    return text


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise UnsafeExpressionError(f"expression contains a disallowed element: {ast.dump(node)}")


def estimate_premium(expression: str) -> float:
    """Evaluate a simple arithmetic premium-estimate expression, e.g.
    "450 * 1.15" for a base premium times a risk multiplier."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise UnsafeExpressionError(f"could not parse expression: {expression!r}") from e
    result = round(_eval_node(tree.body), 2)
    return validate_premium_result(result)


def search_policy_docs(query: str, index: VectorIndex, llm: LLMBackend, top_k: int = 4) -> dict:
    retrieved = index.search(query, top_k=top_k)
    context = " ".join(r.chunk.text for r in retrieved)
    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=query)
    answer = llm.generate(prompt)
    source_doc_ids = []
    for r in retrieved:
        if r.chunk.doc_id not in source_doc_ids:
            source_doc_ids.append(r.chunk.doc_id)
    return {"answer": answer, "sources": source_doc_ids}
