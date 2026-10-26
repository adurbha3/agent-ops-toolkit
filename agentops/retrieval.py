"""A small in-memory embedding index over the insurance-policy corpus, used
as the Claims FAQ agent's document-search tool."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from agentops.corpus import Document, DOCUMENTS

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    text: str


def build_chunks(documents: list[Document] = DOCUMENTS) -> list[Chunk]:
    chunks = []
    for doc in documents:
        for i, sentence in enumerate(s.strip() for s in _SENTENCE_SPLIT.split(doc.text.strip()) if s.strip()):
            chunks.append(Chunk(f"{doc.doc_id}::{i}", doc.doc_id, doc.title, sentence))
    return chunks


@lru_cache(maxsize=1)
def _load_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> np.ndarray:
    embedder = _load_embedder()
    return np.asarray(embedder.encode(texts, normalize_embeddings=True), dtype=np.float32)


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float


class VectorIndex:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vectors = embed_texts([c.text for c in chunks]) if chunks else np.zeros((0, 384))

    @classmethod
    def from_corpus(cls) -> "VectorIndex":
        return cls(build_chunks())

    def search(self, query: str, top_k: int = 4) -> list[ScoredChunk]:
        if not self.chunks:
            return []
        query_vec = embed_texts([query])[0]
        scores = self.vectors @ query_vec
        top_indices = np.argsort(-scores)[:top_k]
        return [ScoredChunk(self.chunks[i], float(scores[i])) for i in top_indices]
