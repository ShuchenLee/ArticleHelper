from app.models.domain import ChunkRecord
from app.services.retrieval_service import search_chunks, tokenize


def _chunk(chunk_id: str, text: str, section: str = "Methods") -> ChunkRecord:
    return ChunkRecord(
        id=chunk_id,
        paper_id="paper-1",
        section=section,
        page_start=1,
        page_end=1,
        chunk_index=int(chunk_id[-1]),
        text=text,
    )


def test_tokenize_supports_english_and_chinese():
    assert tokenize("Method 方法 A/B") == ["method", "方", "法", "a", "b"]


def test_search_chunks_returns_best_matching_chunk_first():
    chunks = [
        _chunk("chunk-0", "The method uses retrieval augmented generation."),
        _chunk("chunk-1", "The conclusion discusses limitations.", "Conclusion"),
    ]

    results = search_chunks("retrieval method", chunks)

    assert results[0].chunk.id == "chunk-0"
    assert results[0].score > 0
