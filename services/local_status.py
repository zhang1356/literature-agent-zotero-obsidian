from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import config
from config import Settings
from logger import get_logger


logger = get_logger(__name__)
__test__ = False


def mask_secret(value: str) -> str:
    value = value.strip()
    if not value:
        return "未配置"
    if len(value) <= 8:
        return "****"
    return f"{value[:3]}-****{value[-4:]}"


def check_obsidian_path_status(vault_path: str) -> dict:
    if not vault_path.strip():
        logger.warning("Obsidian Vault Path 未配置")
        return {"ok": False, "status": "missing", "message": "Obsidian Vault Path 未配置。"}
    path = Path(vault_path).expanduser()
    if not path.exists() or not path.is_dir():
        logger.warning("Obsidian Vault Path 不存在：%s", path)
        return {"ok": False, "status": "invalid", "message": f"Obsidian Vault Path 不存在：{path}"}
    return {"ok": True, "status": "ok", "message": "Obsidian Vault 路径有效。"}


def _dependency_status(names: list[str]) -> dict:
    results = {}
    for name in names:
        results[name] = importlib.util.find_spec(name) is not None
    return results


def _ensure_dir(path: Path) -> dict:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return {"ok": True, "path": path.as_posix(), "message": "可用"}
    except Exception as exc:
        logger.exception("本地目录创建失败：%s; %s", path, exc)
        return {"ok": False, "path": path.as_posix(), "message": str(exc)}


def check_local_environment(active_settings: Settings | None = None) -> dict:
    active_settings = active_settings or config.get_settings()
    config_result = config.validate_user_config()
    dependency_names = ["streamlit", "requests", "pandas", "pyzotero"]
    dependencies = _dependency_status(dependency_names)
    data_dir = _ensure_dir(Path("data"))
    logs_dir = _ensure_dir(Path("logs"))

    obsidian = check_obsidian_path_status(active_settings.obsidian_vault_path)
    zotero_missing = [
        field
        for field, value in {
            "zotero_library_id": active_settings.zotero_library_id,
            "zotero_library_type": active_settings.zotero_library_type,
            "zotero_api_key": active_settings.zotero_api_key,
        }.items()
        if not str(value).strip()
    ]
    model_missing = [
        field
        for field, value in {
            "openai_api_key": active_settings.openai_api_key,
            "openai_base_url": active_settings.openai_base_url,
            "openai_model": active_settings.openai_model,
        }.items()
        if not str(value).strip()
    ]

    checks = {
        "python": {
            "ok": sys.version_info >= (3, 10),
            "message": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "dependencies": {
            "ok": all(dependencies.values()),
            "items": dependencies,
            "message": "关键依赖可导入" if all(dependencies.values()) else "部分关键依赖不可导入",
        },
        "config_example": {
            "ok": Path("config/user_config.example.json").exists(),
            "message": "存在" if Path("config/user_config.example.json").exists() else "不存在",
        },
        "config_user": {
            "ok": config_result["ok"],
            "message": "已配置" if config_result["ok"] else "未完整配置",
            "missing_fields": config_result["missing_fields"],
        },
        "obsidian": obsidian,
        "zotero": {
            "ok": not zotero_missing,
            "status": "ok" if not zotero_missing else "missing",
            "message": "Zotero 配置完整。" if not zotero_missing else "Zotero 尚未配置，当前只能生成本地 Obsidian 笔记。",
            "missing_fields": zotero_missing,
        },
        "model_api": {
            "ok": not model_missing,
            "status": "ok" if not model_missing else "missing",
            "message": "模型 API 已配置。" if not model_missing else _model_missing_message(model_missing),
            "missing_fields": model_missing,
            "api_key": mask_secret(active_settings.openai_api_key),
        },
        "data_dir": data_dir,
        "logs_dir": logs_dir,
        "default_start_year": {
            "ok": True,
            "message": str(active_settings.default_start_year),
        },
    }
    warnings = list(config_result["warnings"])
    for name, ok in dependencies.items():
        if not ok:
            warnings.append(f"依赖不可导入：{name}")
    if model_missing:
        warnings.append(_model_missing_message(model_missing))
    if zotero_missing:
        warnings.append("Zotero 尚未配置，当前只能生成本地 Obsidian 笔记。")
    if not obsidian["ok"]:
        warnings.append(obsidian["message"])

    return {
        "ok": all(item.get("ok", False) for item in checks.values() if isinstance(item, dict)),
        "checks": checks,
        "warnings": warnings,
        "config": config_result,
    }


def _model_missing_message(missing_fields: list[str]) -> str:
    messages = []
    if "openai_api_key" in missing_fields:
        messages.append("模型 API Key 未配置，将使用启发式评分。")
    if "openai_base_url" in missing_fields:
        messages.append("模型 Base URL 未配置。")
    if "openai_model" in missing_fields:
        messages.append("模型名未配置。")
    return " ".join(messages)
