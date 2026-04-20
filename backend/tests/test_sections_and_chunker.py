from app.services.chunker import build_chunks
from app.services.paper_parser import ParsedPage
from app.services.section_detector import detect_sections, normalize_heading


def test_normalize_heading_handles_numbered_sections():
    assert normalize_heading("1 Introduction") == "Introduction"
    assert normalize_heading("2.1 Experimental Setup") == "Experiments"
    assert normalize_heading("References") == "References"


def test_detect_sections_preserves_pages():
    pages = [
        ParsedPage(1, "A Paper Title\nAbstract\nThis paper studies agents."),
        ParsedPage(2, "1 Introduction\nReading papers is difficult."),
    ]

    sections = detect_sections(pages)

    assert [section.title for section in sections] == ["Front Matter", "Abstract", "Introduction"]
    assert sections[1].page_start == 1
    assert sections[2].page_start == 2


def test_build_chunks_keeps_metadata_and_order():
    long_text = "Abstract\n" + " ".join(f"word{i}" for i in range(130))
    chunks = build_chunks("paper-1", [ParsedPage(1, long_text)], max_words=50, overlap_words=10)

    assert len(chunks) == 3
    assert chunks[0].id == "paper-1-chunk-0000"
    assert chunks[0].chunk_index == 0
    assert chunks[0].section == "Abstract"
    assert chunks[0].page_start == 1
    assert "word0" in chunks[0].text
    assert "word40" in chunks[1].text
