from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_release import check_zip


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "LiteratureAgent_Windows.zip"

INCLUDE_FILES = [
    "app.py",
    "config.py",
    "database.py",
    "logger.py",
    "models.py",
    "requirements.txt",
    "README.md",
    "config/user_config.example.json",
]

INCLUDE_DIRS = [
    "agents",
    "connectors",
    "services",
    "ui",
]

ROOT_PACKAGING_FILES = {
    "packaging/setup.bat": "setup.bat",
    "packaging/start.bat": "start.bat",
    "packaging/stop.bat": "stop.bat",
    "packaging/README_朋友使用说明.md": "README_朋友使用说明.md",
}

PACKAGE_HELPER_FILES = [
    "packaging/build_package.py",
    "packaging/check_release.py",
    "packaging/create_desktop_shortcut.ps1",
]

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "tests",
    "build",
    "dist",
}

EXCLUDED_NAMES = {
    ".env",
    "user_config.json",
    "literature_agent.db",
}

EXCLUDED_SUFFIXES = {
    ".db",
    ".log",
    ".pyc",
    ".zip",
}


def should_exclude(path: Path) -> bool:
    relative = path.relative_to(PROJECT_ROOT)
    parts = set(relative.parts)
    if parts & EXCLUDED_PARTS:
        return True
    if path.name in EXCLUDED_NAMES:
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if relative.parts and relative.parts[0] in {"data", "logs"}:
        return True
    return False


def add_file(archive: zipfile.ZipFile, source: Path, archive_name: str | None = None) -> None:
    if should_exclude(source):
        return
    archive.write(source, archive_name or source.relative_to(PROJECT_ROOT).as_posix())


def add_dir(archive: zipfile.ZipFile, directory: Path) -> None:
    for source in directory.rglob("*"):
        if source.is_file():
            add_file(archive, source)


def build_package(output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    output_path = Path(output_path)
    if output_path.exists():
        output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative_file in INCLUDE_FILES:
            add_file(archive, PROJECT_ROOT / relative_file)
        for directory in INCLUDE_DIRS:
            add_dir(archive, PROJECT_ROOT / directory)
        for source, archive_name in ROOT_PACKAGING_FILES.items():
            archive.write(PROJECT_ROOT / source, archive_name)
        for source in PACKAGE_HELPER_FILES:
            add_file(archive, PROJECT_ROOT / source)

    ok, errors, _ = check_zip(output_path)
    if not ok:
        output_path.unlink(missing_ok=True)
        message = "发布安全检查失败，已删除生成的 zip：\n" + "\n".join(
            f"- {error}" for error in errors
        )
        raise RuntimeError(message)
    return output_path


if __name__ == "__main__":
    package_path = build_package()
    ok, _, top_level = check_zip(package_path)
    print(f"已生成：{package_path}")
    print("zip 顶层文件：")
    for item in top_level:
        print(f"- {item}")
    print(f"敏感文件检查：{'通过' if ok else '失败'}")
