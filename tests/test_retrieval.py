import numpy as np

from agentops.retrieval import Chunk, VectorIndex, embed_texts, build_chunks
from agentops.corpus import DOCUMENTS


def test_embed_texts_returns_normalized_vectors():
    vectors = embed_texts(["hello world", "insurance policy"])
    norms = np.linalg.norm(vectors, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-5)


def test_vector_index_ranks_relevant_chunk_first():
    chunks = [
        Chunk("a::0", "a", "Cooking", "A recipe for baking bread requires flour and yeast."),
        Chunk("b::0", "b", "Deductible", "A deductible is paid out of pocket before insurance covers the rest."),
        Chunk("c::0", "c", "Sports", "The basketball team won the championship game."),
    ]
    index = VectorIndex(chunks)
    results = index.search("How much do I pay before insurance kicks in?", top_k=1)
    assert results[0].chunk.doc_id == "b"


def test_build_chunks_covers_every_document():
    chunks = build_chunks()
    doc_ids = {c.doc_id for c in chunks}
    assert doc_ids == {doc.doc_id for doc in DOCUMENTS}


def test_empty_index_returns_no_results():
    assert VectorIndex([]).search("anything") == []
