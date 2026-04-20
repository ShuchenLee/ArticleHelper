from __future__ import annotations

from pydantic import BaseModel


class PaperUploadResponse(BaseModel):
    paper_id: str
    status: str
    title: str | None = None
    language: str | None = None


class PaperStatusResponse(BaseModel):
    paper_id: str
    status: str
    title: str | None = None
    language: str | None = None


class CitationResponse(BaseModel):
    chunk_id: str
    section: str | None
    page_start: int
    page_end: int


class ChatRequest(BaseModel):
    message: str
    selected_text: str | None = None
    current_page: int | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]


class PageResponse(BaseModel):
    paper_id: str
    page_number: int
    text: str
