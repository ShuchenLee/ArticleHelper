import pytest

from app.models.domain import ChunkRecord
from app.services.vector_retrieval_service import (
    build_chunk_embeddings,
    cosine_similarity,
    search_chunks_by_embedding,
    search_chunks_hybrid,
)


class FakeEmbeddingClient:
    def embed_texts(self, texts):
        vectors = {
            "alpha method": [1.0, 0.0],
            "beta result": [0.0, 1.0],
            "method question": [1.0, 0.0],
        }
        return [vectors[text] for text in texts]


class FailingEmbeddingClient:
    def embed_texts(self, texts):
        raise RuntimeError("embedding service unavailable")


def _chunk(index: int, text: str) -> ChunkRecord:
    return ChunkRecord(
        id=f"chunk-{index}",
        paper_id="paper-1",
        section="Methods",
        page_start=index + 1,
        page_end=index + 1,
        chunk_index=index,
        text=text,
    )


def test_cosine_similarity_scores_identical_vector_as_one():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_build_chunk_embeddings_preserves_chunk_ids():
    chunks = [_chunk(0, "alpha method"), _chunk(1, "beta result")]

    records = build_chunk_embeddings(
        chunks,
        embedding_client=FakeEmbeddingClient(),
        model="text-embedding-test",
        batch_size=1,
    )

    assert [record.chunk_id for record in records] == ["chunk-0", "chunk-1"]
    assert records[0].embedding == [1.0, 0.0]


def test_search_chunks_by_embedding_returns_nearest_chunk():
    chunks = [_chunk(0, "alpha method"), _chunk(1, "beta result")]
    records = build_chunk_embeddings(
        chunks,
        embedding_client=FakeEmbeddingClient(),
        model="text-embedding-test",
    )

    results = search_chunks_by_embedding(
        "method question",
        chunks,
        records,
        embedding_client=FakeEmbeddingClient(),
    )

    assert results[0].chunk.id == "chunk-0"


def test_hybrid_search_falls_back_to_lexical_when_embedding_fails():
    chunks = [
        _chunk(0, "alpha method"),
        _chunk(1, "beta result"),
    ]
    records = build_chunk_embeddings(
        chunks,
        embedding_client=FakeEmbeddingClient(),
        model="text-embedding-test",
    )

    results = search_chunks_hybrid(
        "beta",
        chunks,
        records,
        embedding_client=FailingEmbeddingClient(),
    )

    assert results[0].chunk.id == "chunk-1"
