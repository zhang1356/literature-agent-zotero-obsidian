import importlib
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def clear_config_env(monkeypatch):
    for key in [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "ZOTERO_LIBRARY_ID",
        "ZOTERO_LIBRARY_TYPE",
        "ZOTERO_API_KEY",
        "OBSIDIAN_VAULT_PATH",
        "OBSIDIAN_LITERATURE_FOLDER",
        "APP_DATABASE_PATH",
    ]:
        monkeypatch.delenv(key, raising=False)


def reload_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    import config

    return importlib.reload(config)


def test_user_config_json_has_priority_over_env(monkeypatch, tmp_path):
    clear_config_env(monkeypatch)
    monkeypatch.setenv("OPENAI_MODEL", "env-model")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "D:/env-vault")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "user_config.json").write_text(
        json.dumps(
            {
                "openai_model": "json-model",
                "obsidian_vault_path": "D:/json-vault",
                "app_database_path": "./data/from-json.db",
            }
        ),
        encoding="utf-8",
    )

    config = reload_config(monkeypatch, tmp_path)
    settings = config.get_settings()

    assert settings.openai_model == "json-model"
    assert settings.obsidian_vault_path == "D:/json-vault"
    assert settings.app_database_path == "./data/from-json.db"


def test_missing_user_config_json_uses_defaults_without_crashing(monkeypatch, tmp_path):
    clear_config_env(monkeypatch)

    config = reload_config(monkeypatch, tmp_path)
    settings = config.get_settings()

    assert settings.openai_model == "qwen-plus"
    assert settings.zotero_library_type == "user"
    assert settings.app_database_path == "./data/literature_agent.db"
