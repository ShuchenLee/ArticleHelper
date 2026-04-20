from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PaperRecord:
    id: str
    title: str | None
    authors: str | None
    language: str | None
    file_path: str
    status: str
    created_at: str


@dataclass(frozen=True)
class PageRecord:
    id: str
    paper_id: str
    page_number: int
    text: str


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    paper_id: str
    section: str | None
    page_start: int
    page_end: int
    chunk_index: int
    text: str


@dataclass(frozen=True)
class ChatMessageRecord:
    id: str
    paper_id: str
    role: str
    content: str
    created_at: str
