from __future__ import annotations

from fastapi import FastAPI

from app.api import chat, papers
from app.core.config import settings
from app.storage.database import Database


def create_app() -> FastAPI:
    settings.ensure_directories()
    Database(settings.db_path).init_db()

    app = FastAPI(title="ArticleViewer", version="0.1.0")
    app.include_router(papers.router)
    app.include_router(chat.router)

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
