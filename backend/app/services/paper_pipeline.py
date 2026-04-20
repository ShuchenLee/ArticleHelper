from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.models.domain import PageRecord
from app.services.chunker import build_chunks
from app.services.paper_parser import parse_pdf
from app.services.vector_retrieval_service import EmbeddingClient, build_chunk_embeddings
from app.storage.database import Database


def ingest_pdf(
    *,
    source_path: Path,
    original_filename: str,
    database: Database,
    upload_dir: Path,
    embedding_client: EmbeddingClient | None = None,
    embedding_model: str | None = None,
) -> str:
    paper_id = str(uuid.uuid4())
    destination = upload_dir / f"{paper_id}{Path(original_filename).suffix.lower()}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)

    database.create_paper(
        paper_id=paper_id,
        file_path=str(destination),
        status="parsing",
    )

    parsed = parse_pdf(destination)
    database.insert_pages(
        [
            PageRecord(
                id=f"{paper_id}-page-{page.page_number:04d}",
                paper_id=paper_id,
                page_number=page.page_number,
                text=page.text,
            )
            for page in parsed.pages
        ]
    )
    chunks = build_chunks(paper_id, parsed.pages)
    database.insert_chunks(chunks)
    if embedding_client and embedding_model and chunks:
        embeddings = build_chunk_embeddings(
            chunks,
            embedding_client=embedding_client,
            model=embedding_model,
        )
        database.insert_embeddings(embeddings)
    database.update_paper_status(
        paper_id,
        "ready",
        title=parsed.title,
        language=parsed.language,
    )
    return paper_id
