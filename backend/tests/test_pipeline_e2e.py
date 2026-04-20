from pathlib import Path

import pytest

from app.services.chat_agent import answer_from_paper
from app.services.paper_pipeline import ingest_pdf
from app.storage.database import Database

fitz = pytest.importorskip("fitz")


def test_ingest_pdf_then_answer_question(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        (
            "A Useful Method for Reading Papers\n"
            "Abstract\n"
            "This paper studies literature reading agents.\n"
            "Methods\n"
            "The method uses retrieval augmented generation to answer questions."
        ),
    )
    document.save(pdf_path)
    document.close()

    database = Database(tmp_path / "articleviewer.db")
    database.init_db()

    paper_id = ingest_pdf(
        source_path=pdf_path,
        original_filename="sample.pdf",
        database=database,
        upload_dir=tmp_path / "uploads",
    )

    paper = database.get_paper(paper_id)
    assert paper is not None
    assert paper.status == "ready"

    chunks = database.list_chunks(paper_id)
    assert chunks

    answer = answer_from_paper(
        "What method answers questions?",
        title=paper.title,
        chunks=chunks,
    )
    assert answer.citations
    assert "Methods" in answer.answer
