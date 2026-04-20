from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.papers import get_database
from app.models.api import ChatRequest, ChatResponse, CitationResponse
from app.services.chat_agent import answer_from_paper
from app.services.qwen_client import build_qwen_client
from app.core.config import settings
from app.services.vector_retrieval_service import search_chunks_hybrid


router = APIRouter(prefix="/api/papers", tags=["chat"])


@router.post("/{paper_id}/chat", response_model=ChatResponse)
def chat_with_paper(paper_id: str, request: ChatRequest) -> ChatResponse:
    database = get_database()
    paper = database.get_paper(paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if paper.status != "ready":
        raise HTTPException(status_code=409, detail=f"Paper is not ready: {paper.status}")

    chunks = database.list_chunks(paper_id)
    qwen_client = build_qwen_client(
        api_key=settings.api_key,
        base_url=settings.api_base_url,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
    )
    embeddings = database.list_embeddings(paper_id)
    search_results = search_chunks_hybrid(
        request.message,
        chunks,
        embeddings,
        embedding_client=qwen_client if settings.has_embedding_config else None,
    )

    database.add_message(paper_id, "user", request.message)
    answer = answer_from_paper(
        request.message,
        title=paper.title,
        chunks=chunks,
        selected_text=request.selected_text,
        llm_client=qwen_client,
        search_results=search_results,
    )
    database.add_message(paper_id, "assistant", answer.answer)

    return ChatResponse(
        answer=answer.answer,
        citations=[
            CitationResponse(
                chunk_id=citation.chunk_id,
                section=citation.section,
                page_start=citation.page_start,
                page_end=citation.page_end,
            )
            for citation in answer.citations
        ],
    )
