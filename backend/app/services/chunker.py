from __future__ import annotations

import re
from typing import Iterable

from app.models.domain import ChunkRecord
from app.services.paper_parser import ParsedPage
from app.services.section_detector import SectionSpan, detect_sections


def build_chunks(
    paper_id: str,
    pages: list[ParsedPage],
    *,
    max_words: int = 220,
    overlap_words: int = 40,
) -> list[ChunkRecord]:
    sections = detect_sections(pages)
    chunks: list[ChunkRecord] = []
    for section in sections:
        for text in split_section_text(section, max_words=max_words, overlap_words=overlap_words):
            chunks.append(
                ChunkRecord(
                    id=f"{paper_id}-chunk-{len(chunks):04d}",
                    paper_id=paper_id,
                    section=section.title,
                    page_start=section.page_start,
                    page_end=section.page_end,
                    chunk_index=len(chunks),
                    text=text,
                )
            )
    return chunks


def split_section_text(
    section: SectionSpan,
    *,
    max_words: int = 220,
    overlap_words: int = 40,
) -> Iterable[str]:
    words = _tokenize_for_chunking(section.text)
    if len(words) <= max_words:
        yield section.text
        return

    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        if len(words) - end <= overlap_words:
            end = len(words)
        yield " ".join(words[start:end]).strip()
        if end == len(words):
            break
        start = max(end - overlap_words, start + 1)


def _tokenize_for_chunking(text: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?|[^\s]", text)
    return tokens
