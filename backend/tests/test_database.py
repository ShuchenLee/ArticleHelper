from pathlib import Path

from app.models.domain import ChunkRecord, EmbeddingRecord, PageRecord, utc_now_iso
from app.storage.database import Database


def test_database_crud_round_trip(tmp_path: Path):
    database = Database(tmp_path / "articleviewer.db")
    database.init_db()

    paper = database.create_paper(
        paper_id="paper-1",
        file_path="paper.pdf",
        title="Old title",
        status="uploaded",
    )
    assert paper.id == "paper-1"

    database.update_paper_status("paper-1", "ready", title="New title", language="en")
    loaded = database.get_paper("paper-1")
    assert loaded is not None
    assert loaded.status == "ready"
    assert loaded.title == "New title"
    assert loaded.language == "en"

    database.insert_pages(
        [
            PageRecord(id="page-1", paper_id="paper-1", page_number=1, text="Abstract text"),
            PageRecord(id="page-2", paper_id="paper-1", page_number=2, text="Method text"),
        ]
    )
    assert [page.page_number for page in database.list_pages("paper-1")] == [1, 2]

    database.insert_chunks(
        [
            ChunkRecord(
                id="chunk-1",
                paper_id="paper-1",
                section="Abstract",
                page_start=1,
                page_end=1,
                chunk_index=0,
                text="Abstract text",
            )
        ]
    )
    chunks = database.list_chunks("paper-1")
    assert len(chunks) == 1
    assert chunks[0].section == "Abstract"

    database.insert_embeddings(
        [
            EmbeddingRecord(
                chunk_id="chunk-1",
                paper_id="paper-1",
                model="text-embedding-test",
                embedding=[0.1, 0.2, 0.3],
                created_at=utc_now_iso(),
            )
        ]
    )
    embeddings = database.list_embeddings("paper-1")
    assert len(embeddings) == 1
    assert embeddings[0].embedding == [0.1, 0.2, 0.3]

    database.add_message("paper-1", "user", "What is this paper about?")
    database.add_message("paper-1", "assistant", "It is about testing.")
    assert [message.role for message in database.list_messages("paper-1")] == [
        "user",
        "assistant",
    ]
