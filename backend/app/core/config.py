from __future__ import annotations

import os
import re
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
    config_path: Path
    api_base_url: str
    api_key: str | None
    embedding_model: str | None
    llm_model: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        config_path = _resolve_path(
            os.getenv("ARTICLEVIEWER_CONFIG_PATH"),
            REPO_ROOT / "config.txt",
        )
        file_config = load_key_value_config(config_path)
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
            config_path=config_path,
            api_base_url=_setting_value(
                "ARTICLEVIEWER_API_BASE_URL",
                "api_base_url",
                file_config,
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            api_key=_setting_value("ARTICLEVIEWER_API_KEY", "api_key", file_config),
            embedding_model=_setting_value(
                "ARTICLEVIEWER_EMBEDDING_MODEL",
                "embedding_model",
                file_config,
            ),
            llm_model=_setting_value("ARTICLEVIEWER_LLM_MODEL", "llm_model", file_config),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    @property
    def has_llm_config(self) -> bool:
        return bool(self.api_key and self.llm_model)

    @property
    def has_embedding_config(self) -> bool:
        return bool(self.api_key and self.embedding_model)


def load_key_value_config(path: Path | str) -> dict[str, str]:
    config_path = Path(path)
    if not config_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            values[key] = value
    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _setting_value(
    env_key: str,
    file_key: str,
    file_config: dict[str, str],
    default: str | None = None,
) -> str | None:
    value = os.getenv(env_key)
    if value is not None:
        return value
    return file_config.get(file_key, default)


settings = Settings.from_env()
