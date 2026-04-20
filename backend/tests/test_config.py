from pathlib import Path

from app.core.config import Settings, load_key_value_config


def test_load_key_value_config_reads_quoted_values(tmp_path: Path):
    config_path = tmp_path / "config.txt"
    config_path.write_text(
        '\n'.join(
            [
                'embedding_model = "tongyi-embedding-test"',
                'llm_model = "qwen-test"',
                'api_key = "secret"',
                "ignored line",
            ]
        ),
        encoding="utf-8",
    )

    values = load_key_value_config(config_path)

    assert values == {
        "embedding_model": "tongyi-embedding-test",
        "llm_model": "qwen-test",
        "api_key": "secret",
    }


def test_load_key_value_config_handles_utf8_bom(tmp_path: Path):
    config_path = tmp_path / "config.txt"
    config_path.write_text(
        'embedding_model = "text-embedding-v4"\n',
        encoding="utf-8-sig",
    )

    assert load_key_value_config(config_path)["embedding_model"] == "text-embedding-v4"


def test_settings_from_env_uses_config_file(monkeypatch, tmp_path: Path):
    config_path = tmp_path / "config.txt"
    config_path.write_text(
        '\n'.join(
            [
                'embedding_model = "tongyi-embedding-test"',
                'llm_model = "qwen-test"',
                'api_key = "secret"',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ARTICLEVIEWER_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("ARTICLEVIEWER_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("ARTICLEVIEWER_API_KEY", raising=False)
    monkeypatch.delenv("ARTICLEVIEWER_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("ARTICLEVIEWER_LLM_MODEL", raising=False)

    settings = Settings.from_env()

    assert settings.embedding_model == "tongyi-embedding-test"
    assert settings.llm_model == "qwen-test"
    assert settings.api_key == "secret"
    assert settings.has_llm_config
    assert settings.has_embedding_config


def test_environment_overrides_config_file(monkeypatch, tmp_path: Path):
    config_path = tmp_path / "config.txt"
    config_path.write_text('llm_model = "from-file"', encoding="utf-8")
    monkeypatch.setenv("ARTICLEVIEWER_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("ARTICLEVIEWER_LLM_MODEL", "from-env")

    assert Settings.from_env().llm_model == "from-env"
