from __future__ import annotations

import math
from typing import Protocol

from app.models.domain import ChunkRecord, EmbeddingRecord, utc_now_iso
from app.services.retrieval_service import SearchResult, search_chunks


class EmbeddingClient(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


def build_chunk_embeddings(
    chunks: list[ChunkRecord],
    *,
    embedding_client: EmbeddingClient,
    model: str,
    batch_size: int = 16,
) -> list[EmbeddingRecord]:
    records: list[EmbeddingRecord] = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = embedding_client.embed_texts([chunk.text for chunk in batch])
        if len(vectors) != len(batch):
            raise ValueError("Embedding client returned a different number of vectors.")
        records.extend(
            EmbeddingRecord(
                chunk_id=chunk.id,
                paper_id=chunk.paper_id,
                model=model,
                embedding=vector,
                created_at=utc_now_iso(),
            )
            for chunk, vector in zip(batch, vectors)
        )
    return records


def search_chunks_by_embedding(
    query: str,
    chunks: list[ChunkRecord],
    embeddings: list[EmbeddingRecord],
    *,
    embedding_client: EmbeddingClient,
    top_k: int = 5,
) -> list[SearchResult]:
    if not query.strip() or not chunks or not embeddings:
        return []

    query_vectors = embedding_client.embed_texts([query])
    if len(query_vectors) != 1:
        raise ValueError("Embedding client must return one query vector.")
    query_vector = query_vectors[0]

    chunks_by_id = {chunk.id: chunk for chunk in chunks}
    scored: list[SearchResult] = []
    for embedding in embeddings:
        chunk = chunks_by_id.get(embedding.chunk_id)
        if not chunk:
            continue
        score = cosine_similarity(query_vector, embedding.embedding)
        if score > 0:
            scored.append(SearchResult(chunk=chunk, score=score))

    scored.sort(key=lambda result: result.score, reverse=True)
    return scored[:top_k]


def search_chunks_hybrid(
    query: str,
    chunks: list[ChunkRecord],
    embeddings: list[EmbeddingRecord],
    *,
    embedding_client: EmbeddingClient | None,
    top_k: int = 5,
) -> list[SearchResult]:
    if embedding_client and embeddings:
        try:
            vector_results = search_chunks_by_embedding(
                query,
                chunks,
                embeddings,
                embedding_client=embedding_client,
                top_k=top_k,
            )
            if vector_results:
                return vector_results
        except (RuntimeError, ValueError):
            pass
    return search_chunks(query, chunks, top_k=top_k)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
