from __future__ import annotations

import sqlite3
import uuid
import json
from pathlib import Path
from typing import Iterable

from app.models.domain import (
    ChatMessageRecord,
    ChunkRecord,
    EmbeddingRecord,
    PageRecord,
    PaperRecord,
    utc_now_iso,
)


class Database:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_db(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    authors TEXT,
                    language TEXT,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS paper_pages (
                    id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    UNIQUE(paper_id, page_number),
                    FOREIGN KEY(paper_id) REFERENCES papers(id)
                );

                CREATE TABLE IF NOT EXISTS paper_chunks (
                    id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    section TEXT,
                    page_start INTEGER NOT NULL,
                    page_end INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    UNIQUE(paper_id, chunk_index),
                    FOREIGN KEY(paper_id) REFERENCES papers(id)
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(paper_id) REFERENCES papers(id)
                );

                CREATE TABLE IF NOT EXISTS chunk_embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(chunk_id) REFERENCES paper_chunks(id),
                    FOREIGN KEY(paper_id) REFERENCES papers(id)
                );
                """
            )

    def create_paper(
        self,
        *,
        paper_id: str,
        file_path: str,
        title: str | None = None,
        authors: str | None = None,
        language: str | None = None,
        status: str = "uploaded",
    ) -> PaperRecord:
        created_at = utc_now_iso()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO papers (id, title, authors, language, file_path, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (paper_id, title, authors, language, file_path, status, created_at),
            )
        return PaperRecord(paper_id, title, authors, language, file_path, status, created_at)

    def update_paper_status(
        self,
        paper_id: str,
        status: str,
        *,
        title: str | None = None,
        language: str | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE papers
                SET status = ?, title = COALESCE(?, title), language = COALESCE(?, language)
                WHERE id = ?
                """,
                (status, title, language, paper_id),
            )

    def get_paper(self, paper_id: str) -> PaperRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        return _paper_from_row(row) if row else None

    def insert_pages(self, pages: Iterable[PageRecord]) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO paper_pages (id, paper_id, page_number, text)
                VALUES (?, ?, ?, ?)
                """,
                [(page.id, page.paper_id, page.page_number, page.text) for page in pages],
            )

    def list_pages(self, paper_id: str) -> list[PageRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM paper_pages WHERE paper_id = ? ORDER BY page_number",
                (paper_id,),
            ).fetchall()
        return [_page_from_row(row) for row in rows]

    def insert_chunks(self, chunks: Iterable[ChunkRecord]) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO paper_chunks
                (id, paper_id, section, page_start, page_end, chunk_index, text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.id,
                        chunk.paper_id,
                        chunk.section,
                        chunk.page_start,
                        chunk.page_end,
                        chunk.chunk_index,
                        chunk.text,
                    )
                    for chunk in chunks
                ],
            )

    def list_chunks(self, paper_id: str) -> list[ChunkRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM paper_chunks WHERE paper_id = ? ORDER BY chunk_index",
                (paper_id,),
            ).fetchall()
        return [_chunk_from_row(row) for row in rows]

    def insert_embeddings(self, embeddings: Iterable[EmbeddingRecord]) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO chunk_embeddings
                (chunk_id, paper_id, model, embedding_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        embedding.chunk_id,
                        embedding.paper_id,
                        embedding.model,
                        json.dumps(embedding.embedding),
                        embedding.created_at,
                    )
                    for embedding in embeddings
                ],
            )

    def list_embeddings(self, paper_id: str) -> list[EmbeddingRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM chunk_embeddings
                WHERE paper_id = ?
                ORDER BY chunk_id
                """,
                (paper_id,),
            ).fetchall()
        return [_embedding_from_row(row) for row in rows]

    def add_message(self, paper_id: str, role: str, content: str) -> ChatMessageRecord:
        message = ChatMessageRecord(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            role=role,
            content=content,
            created_at=utc_now_iso(),
        )
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_messages (id, paper_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message.id, message.paper_id, message.role, message.content, message.created_at),
            )
        return message

    def list_messages(self, paper_id: str, limit: int = 20) -> list[ChatMessageRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM chat_messages
                WHERE paper_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (paper_id, limit),
            ).fetchall()
        return [_message_from_row(row) for row in reversed(rows)]


def _paper_from_row(row: sqlite3.Row) -> PaperRecord:
    return PaperRecord(
        id=row["id"],
        title=row["title"],
        authors=row["authors"],
        language=row["language"],
        file_path=row["file_path"],
        status=row["status"],
        created_at=row["created_at"],
    )


def _page_from_row(row: sqlite3.Row) -> PageRecord:
    return PageRecord(
        id=row["id"],
        paper_id=row["paper_id"],
        page_number=row["page_number"],
        text=row["text"],
    )


def _chunk_from_row(row: sqlite3.Row) -> ChunkRecord:
    return ChunkRecord(
        id=row["id"],
        paper_id=row["paper_id"],
        section=row["section"],
        page_start=row["page_start"],
        page_end=row["page_end"],
        chunk_index=row["chunk_index"],
        text=row["text"],
    )


def _embedding_from_row(row: sqlite3.Row) -> EmbeddingRecord:
    return EmbeddingRecord(
        chunk_id=row["chunk_id"],
        paper_id=row["paper_id"],
        model=row["model"],
        embedding=json.loads(row["embedding_json"]),
        created_at=row["created_at"],
    )


def _message_from_row(row: sqlite3.Row) -> ChatMessageRecord:
    return ChatMessageRecord(
        id=row["id"],
        paper_id=row["paper_id"],
        role=row["role"],
        content=row["content"],
        created_at=row["created_at"],
    )
