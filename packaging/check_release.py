from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path


SENSITIVE_NAMES = {".env", "user_config.json"}
SENSITIVE_DIRS = {".venv", "__pycache__", ".pytest_cache", "tests", ".git"}
SENSITIVE_SUFFIXES = {".db", ".log"}
SECRET_FILE_SUFFIXES = {
    ".env",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
    ".txt",
}
SECRET_KEY_PATTERN = re.compile(
    r"(?i)(api_key|zotero_api_key|openai_api_key)\s*[:=]\s*[\"']?([^\"'\s,}]+)"
)
PLACEHOLDER_VALUES = {
    "",
    "your_api_key",
    "your-api-key",
    "example",
    "placeholder",
    "sk-xxxx",
    "secret",
}


def _normalized(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def forbidden_path_reason(name: str) -> str | None:
    normalized = _normalized(name)
    parts = normalized.split("/")
    lowered_parts = {part.lower() for part in parts}
    basename = parts[-1].lower()
    suffix = Path(basename).suffix.lower()

    if basename in SENSITIVE_NAMES:
        return "包含本机配置文件"
    if lowered_parts & SENSITIVE_DIRS:
        return "包含运行时、测试或版本控制目录"
    if suffix in SENSITIVE_SUFFIXES:
        return "包含数据库或日志文件"
    if len(parts) >= 2 and parts[0].lower() == "data" and suffix == ".db":
        return "包含 data/*.db"
    if len(parts) >= 2 and parts[0].lower() == "logs" and suffix == ".log":
        return "包含 logs/*.log"
    return None


def has_real_secret(name: str, data: bytes) -> bool:
    suffix = Path(name).suffix.lower()
    if suffix not in SECRET_FILE_SUFFIXES:
        return False
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        return False
    for match in SECRET_KEY_PATTERN.finditer(text):
        value = match.group(2).strip().strip('"').strip("'")
        if value.lower() in PLACEHOLDER_VALUES:
            continue
        if len(value) >= 8:
            return True
    return False


def check_zip(zip_path: str | Path) -> tuple[bool, list[str], list[str]]:
    zip_path = Path(zip_path)
    errors: list[str] = []
    top_level: list[str] = []
    if not zip_path.exists():
        return False, [f"zip 不存在：{zip_path}"], top_level

    try:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            top_level = sorted({name.split("/")[0] for name in names if name})
            for name in names:
                reason = forbidden_path_reason(name)
                if reason:
                    errors.append(f"{name}: {reason}")
                    continue
                if name.endswith("/"):
                    continue
                try:
                    data = archive.read(name)
                except Exception as exc:
                    errors.append(f"{name}: 读取失败：{exc}")
                    continue
                if has_real_secret(name, data):
                    errors.append(f"{name}: 疑似包含真实 API Key 配置")
    except zipfile.BadZipFile:
        return False, [f"不是有效 zip 文件：{zip_path}"], top_level

    return not errors, errors, top_level


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    zip_path = Path(args[0]) if args else Path("LiteratureAgent_Windows.zip")
    ok, errors, top_level = check_zip(zip_path)
    if not ok:
        print("发布安全检查失败：")
        for error in errors:
            print(f"- {error}")
        return 1
    print("发布安全检查通过。")
    print("zip 顶层文件：")
    for item in top_level:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
