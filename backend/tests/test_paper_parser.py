from pathlib import Path

import pytest

from app.services.paper_parser import PaperParseError, detect_language, guess_title, normalize_text, parse_pdf


def test_normalize_text_merges_hyphenated_line_breaks():
    raw = "This is a hyphen-\nated word.\n\n\nNext   line."

    assert normalize_text(raw) == "This is a hyphenated word.\n\nNext line."


def test_guess_title_skips_section_heading():
    text = "Abstract\nA Useful Method for Reading Papers\nAuthors"

    assert guess_title(text) == "A Useful Method for Reading Papers"


def test_detect_language_returns_zh_for_chinese_text():
    assert detect_language("这是一篇中文论文，讨论文献阅读智能体。") == "zh"


def test_parse_pdf_missing_file_has_clear_error(tmp_path: Path):
    with pytest.raises(PaperParseError, match="does not exist"):
        parse_pdf(tmp_path / "missing.pdf")


def test_parse_pdf_rejects_non_pdf(tmp_path: Path):
    text_file = tmp_path / "paper.txt"
    text_file.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(PaperParseError, match="Only PDF"):
        parse_pdf(text_file)
