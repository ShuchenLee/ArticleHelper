from app.models.domain import ChunkRecord
from app.services.summary_service import build_paper_overview, compact_snippet, summarize_section


def _chunk(index: int, section: str, text: str) -> ChunkRecord:
    return ChunkRecord(
        id=f"chunk-{index}",
        paper_id="paper-1",
        section=section,
        page_start=index + 1,
        page_end=index + 1,
        chunk_index=index,
        text=text,
    )


def test_build_paper_overview_extracts_standard_sections():
    chunks = [
        _chunk(0, "Abstract", "Abstract says the paper studies reading agents."),
        _chunk(1, "Methods", "The method retrieves evidence from chunks."),
        _chunk(2, "Conclusion", "The conclusion states the agent helps reading."),
    ]

    overview = build_paper_overview("Paper Title", chunks)

    assert overview.title == "Paper Title"
    assert "reading agents" in overview.abstract
    assert "retrieves evidence" in overview.methods
    assert overview.results is None


def test_summarize_section_returns_none_when_missing():
    assert summarize_section("Results", []) is None


def test_compact_snippet_truncates_long_text():
    snippet = compact_snippet("A" * 1000, max_chars=50)

    assert snippet.endswith("...")
    assert len(snippet) <= 53
