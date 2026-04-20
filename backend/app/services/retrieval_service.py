from __future__ import annotations

import math
import re
from dataclasses import dataclass

from app.models.domain import ChunkRecord


@dataclass(frozen=True)
class SearchResult:
    chunk: ChunkRecord
    score: float


def search_chunks(query: str, chunks: list[ChunkRecord], *, top_k: int = 5) -> list[SearchResult]:
    query_terms = tokenize(query)
    if not query_terms:
        return []

    scored: list[SearchResult] = []
    for chunk in chunks:
        score = score_chunk(query, query_terms, chunk)
        if score > 0:
            scored.append(SearchResult(chunk=chunk, score=score))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def score_chunk(query: str, query_terms: list[str], chunk: ChunkRecord) -> float:
    chunk_terms = tokenize(chunk.text)
    if not chunk_terms:
        return 0.0

    query_set = set(query_terms)
    chunk_set = set(chunk_terms)
    overlap = query_set & chunk_set
    if not overlap:
        return 0.0

    term_frequency = sum(chunk_terms.count(term) for term in overlap)
    coverage = len(overlap) / max(len(query_set), 1)
    density = term_frequency / math.sqrt(len(chunk_terms))
    phrase_bonus = 1.5 if query.strip().lower() in chunk.text.lower() else 0.0
    section_bonus = _section_bonus(query_terms, chunk.section)
    return coverage * 3.0 + density + phrase_bonus + section_bonus


def tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
        if token.strip()
    ]


def _section_bonus(query_terms: list[str], section: str | None) -> float:
    if not section:
        return 0.0
    section_terms = set(tokenize(section))
    if section_terms & set(query_terms):
        return 0.75
    aliases = {
        "method": {"method", "methods", "approach", "算法", "方法"},
        "experiment": {"experiment", "experiments", "evaluation", "实验", "结果"},
        "conclusion": {"conclusion", "conclusions", "结论"},
    }
    section_lower = section.lower()
    for section_key, terms in aliases.items():
        if section_key in section_lower and terms & set(query_terms):
            return 0.5
    return 0.0
