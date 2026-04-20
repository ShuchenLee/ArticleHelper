from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    db_path: Path
    upload_dir: Path
    index_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = _resolve_path(
            os.getenv("ARTICLEVIEWER_DATA_DIR"),
            REPO_ROOT / "data",
        )
        return cls(
            data_dir=data_dir,
            db_path=_resolve_path(
                os.getenv("ARTICLEVIEWER_DB_PATH"),
                data_dir / "sqlite" / "articleviewer.db",
            ),
            upload_dir=_resolve_path(
                os.getenv("ARTICLEVIEWER_UPLOAD_DIR"),
                data_dir / "uploads",
            ),
            index_dir=_resolve_path(
                os.getenv("ARTICLEVIEWER_INDEX_DIR"),
                data_dir / "indexes",
            ),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)


settings = Settings.from_env()
