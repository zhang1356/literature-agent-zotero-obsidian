from __future__ import annotations

import uuid
from pathlib import Path

import httpx

from config import Settings
from connectors.obsidian_connector import (
    LOCAL_ANALYZED_FOLDER,
    LOCAL_BASE_FOLDER,
    LOCAL_INBOX_FOLDER,
    LOCAL_LOGS_FOLDER,
)
from connectors.zotero_connector import ZoteroConnector
from logger import get_logger


logger = get_logger(__name__)
__test__ = False


def _friendly_error(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()
    if "permission" in lowered or "forbidden" in lowered or "403" in lowered:
        return "Zotero 权限不足：请检查 API Key 是否开启写入权限。"
    if "unauthorized" in lowered or "401" in lowered or "api key" in lowered:
        return "API Key 可能不正确，请检查后重试。"
    if "timed out" in lowered or "timeout" in lowered or "network" in lowered:
        return "网络异常：请检查网络连接后重试。"
    return "连接测试失败，请检查配置是否正确。"


def test_obsidian_path(vault_path: str, literature_folder: str) -> tuple[bool, str]:
    if not vault_path.strip():
        logger.warning("Obsidian 路径未配置")
        return False, "Obsidian 路径未配置或不存在，请先填写有效 Vault Path。"

    root = Path(vault_path).expanduser()
    if not root.exists() or not root.is_dir():
        logger.warning("Obsidian 路径不存在或不是目录：%s", root)
        return False, "Obsidian 路径不存在或没有写入权限。"

    test_file: Path | None = None
    try:
        base_dir = root / LOCAL_BASE_FOLDER
        literature_dir = base_dir / LOCAL_INBOX_FOLDER
        (base_dir / LOCAL_ANALYZED_FOLDER).mkdir(parents=True, exist_ok=True)
        (base_dir / LOCAL_LOGS_FOLDER).mkdir(parents=True, exist_ok=True)
        literature_dir.mkdir(parents=True, exist_ok=True)
        test_file = literature_dir / f".literature_agent_test_{uuid.uuid4().hex}.tmp"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return True, "Obsidian 路径可用。"
    except Exception as exc:
        logger.exception("Obsidian 路径测试失败：%s", exc)
        if test_file and test_file.exists():
            try:
                test_file.unlink()
            except Exception:
                logger.warning("Obsidian 测试临时文件删除失败：%s", test_file)
        return False, "Obsidian 路径不存在或没有写入权限。"


def test_zotero_connection(settings: Settings) -> tuple[bool, str]:
    if not (
        settings.zotero_library_id.strip()
        and settings.zotero_library_type.strip()
        and settings.zotero_api_key.strip()
    ):
        logger.warning("Zotero 配置缺失，无法测试连接")
        return False, "请先填写 Zotero Library ID、Library Type 和 API Key。"

    try:
        connector = ZoteroConnector(
            settings.zotero_library_id,
            settings.zotero_library_type,
            settings.zotero_api_key,
        )
        connector.get_recent_items(limit=1)
        return True, "Zotero 连接正常。"
    except Exception as exc:
        logger.exception("Zotero 连接测试失败：%s", exc)
        return False, _friendly_error(exc)


def test_model_api(settings: Settings) -> tuple[bool, str]:
    if not (
        settings.openai_api_key.strip()
        and settings.openai_base_url.strip()
        and settings.openai_model.strip()
    ):
        logger.warning("模型 API 配置缺失，无法测试连接")
        return False, "请先填写 API Key、Base URL 和模型名称。"

    endpoint = settings.openai_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.openai_model,
        "messages": [{"role": "user", "content": "ping"}],
        "temperature": 0,
        "max_tokens": 1,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
        return True, "模型 API 可用。"
    except Exception as exc:
        logger.exception("模型 API 测试失败：%s", exc)
        return (
            False,
            "模型 API 不可用。可能原因：API Key 错误、Base URL 错误、模型名称错误或网络不可用。",
        )
