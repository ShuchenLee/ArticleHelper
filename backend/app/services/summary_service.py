from __future__ import annotations

from dataclasses import dataclass

from app.models.domain import ChunkRecord


@dataclass(frozen=True)
class PaperOverview:
    title: str | None
    abstract: str | None
    methods: str | None
    results: str | None
    conclusion: str | None
    limitations: str | None


def build_paper_overview(title: str | None, chunks: list[ChunkRecord]) -> PaperOverview:
    return PaperOverview(
        title=title,
        abstract=_first_snippet(chunks, "Abstract"),
        methods=_first_snippet(chunks, "Methods"),
        results=_first_snippet(chunks, "Results") or _first_snippet(chunks, "Experiments"),
        conclusion=_first_snippet(chunks, "Conclusion"),
        limitations=_first_snippet(chunks, "Limitations"),
    )


def summarize_section(section_name: str, chunks: list[ChunkRecord], *, max_chars: int = 900) -> str | None:
    section_chunks = [
        chunk
        for chunk in chunks
        if chunk.section and chunk.section.lower() == section_name.lower()
    ]
    if not section_chunks:
        return None

    text = " ".join(chunk.text for chunk in section_chunks)
    return compact_snippet(text, max_chars=max_chars)


def compact_snippet(text: str, *, max_chars: int = 700) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned

    cutoff = cleaned.rfind(".", 0, max_chars)
    if cutoff < max_chars * 0.45:
        cutoff = max_chars
    return cleaned[:cutoff].rstrip(" ,;:") + "..."


def _first_snippet(chunks: list[ChunkRecord], section_name: str) -> str | None:
    for chunk in chunks:
        if chunk.section == section_name:
            return compact_snippet(chunk.text)
    return None
