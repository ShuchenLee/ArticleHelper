from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat, papers
from app.core.config import REPO_ROOT, settings
from app.storage.database import Database


def create_app() -> FastAPI:
    settings.ensure_directories()
    Database(settings.db_path).init_db()

    app = FastAPI(title="ArticleViewer", version="0.1.0")
    app.include_router(papers.router)
    app.include_router(chat.router)

    frontend_dir = REPO_ROOT / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(frontend_dir / "index.html")

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
