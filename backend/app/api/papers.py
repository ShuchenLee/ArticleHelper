from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.models.api import PageResponse, PaperStatusResponse, PaperUploadResponse
from app.services.paper_parser import PaperParseError
from app.services.paper_pipeline import ingest_pdf
from app.services.qwen_client import QwenClientError, build_qwen_client
from app.storage.database import Database


router = APIRouter(prefix="/api/papers", tags=["papers"])


def get_database() -> Database:
    database = Database(settings.db_path)
    database.init_db()
    return database


@router.post("/upload", response_model=PaperUploadResponse)
async def upload_paper(file: UploadFile = File(...)) -> PaperUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    settings.ensure_directories()
    database = get_database()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await file.read())

    try:
        qwen_client = build_qwen_client(
            api_key=settings.api_key,
            base_url=settings.api_base_url,
            llm_model=settings.llm_model,
            embedding_model=settings.embedding_model,
        )
        paper_id = ingest_pdf(
            source_path=temp_path,
            original_filename=file.filename,
            database=database,
            upload_dir=settings.upload_dir,
            embedding_client=qwen_client if settings.has_embedding_config else None,
            embedding_model=settings.embedding_model,
        )
    except PaperParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except QwenClientError as exc:
        raise HTTPException(status_code=502, detail=f"Embedding API failed: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)

    paper = database.get_paper(paper_id)
    if paper is None:
        raise HTTPException(status_code=500, detail="Paper was not saved.")
    return PaperUploadResponse(
        paper_id=paper.id,
        status=paper.status,
        title=paper.title,
        language=paper.language,
    )


@router.get("/{paper_id}/status", response_model=PaperStatusResponse)
def get_paper_status(paper_id: str) -> PaperStatusResponse:
    paper = get_database().get_paper(paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return PaperStatusResponse(
        paper_id=paper.id,
        status=paper.status,
        title=paper.title,
        language=paper.language,
    )


@router.get("/{paper_id}/pages/{page_number}", response_model=PageResponse)
def get_page(paper_id: str, page_number: int) -> PageResponse:
    pages = get_database().list_pages(paper_id)
    for page in pages:
        if page.page_number == page_number:
            return PageResponse(paper_id=paper_id, page_number=page.page_number, text=page.text)
    raise HTTPException(status_code=404, detail="Page not found.")
