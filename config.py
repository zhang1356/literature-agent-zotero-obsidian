import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()

CONFIG_DIR = Path("config")
USER_CONFIG_PATH = CONFIG_DIR / "user_config.json"
DEFAULT_START_YEAR = 2026

DEFAULT_VALUES = {
    "openai_api_key": "",
    "openai_base_url": "",
    "openai_model": "qwen-plus",
    "zotero_library_id": "",
    "zotero_library_type": "user",
    "zotero_api_key": "",
    "obsidian_vault_path": "",
    "obsidian_literature_folder": "Literature Notes",
    "app_database_path": "./data/literature_agent.db",
    "default_start_year": DEFAULT_START_YEAR,
}

ENV_MAP = {
    "openai_api_key": "OPENAI_API_KEY",
    "openai_base_url": "OPENAI_BASE_URL",
    "openai_model": "OPENAI_MODEL",
    "zotero_library_id": "ZOTERO_LIBRARY_ID",
    "zotero_library_type": "ZOTERO_LIBRARY_TYPE",
    "zotero_api_key": "ZOTERO_API_KEY",
    "obsidian_vault_path": "OBSIDIAN_VAULT_PATH",
    "obsidian_literature_folder": "OBSIDIAN_LITERATURE_FOLDER",
    "app_database_path": "APP_DATABASE_PATH",
    "default_start_year": "DEFAULT_START_YEAR",
}


class Settings(BaseModel):
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "qwen-plus"

    zotero_library_id: str = ""
    zotero_library_type: str = "user"
    zotero_api_key: str = ""

    obsidian_vault_path: str = ""
    obsidian_literature_folder: str = "Literature Notes"

    app_database_path: str = "./data/literature_agent.db"
    default_start_year: int = DEFAULT_START_YEAR

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def has_zotero(self) -> bool:
        return bool(self.zotero_library_id.strip() and self.zotero_api_key.strip())

    @property
    def has_obsidian(self) -> bool:
        return bool(self.obsidian_vault_path.strip())


@lru_cache
def get_settings() -> Settings:
    values = DEFAULT_VALUES.copy()
    for field_name, env_name in ENV_MAP.items():
        env_value = os.getenv(env_name)
        if env_value is not None:
            values[field_name] = env_value
    values.update(load_user_config())
    return Settings(**values)


def load_user_config(path: Path | None = None) -> dict:
    config_path = path or USER_CONFIG_PATH
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"配置文件不是有效 JSON：{config_path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是 JSON 对象：{config_path}")
    return {key: value for key, value in data.items() if key in DEFAULT_VALUES}


def save_user_config(data: dict, path: Path | None = None) -> Path:
    config_path = path or USER_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = DEFAULT_VALUES.copy()
    payload.update({key: value for key, value in data.items() if key in DEFAULT_VALUES})
    config_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    get_settings.cache_clear()
    global settings
    settings = get_settings()
    return config_path


def settings_as_dict(current_settings: Settings | None = None) -> dict:
    value = current_settings or get_settings()
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value.dict()


settings = get_settings()
