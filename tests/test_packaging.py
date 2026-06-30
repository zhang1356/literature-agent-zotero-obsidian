import sys
import zipfile
import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_package_excludes_local_secrets_and_runtime_files(tmp_path):
    module_path = PROJECT_ROOT / "packaging" / "build_package.py"
    spec = importlib.util.spec_from_file_location("build_package", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    build_package = module.build_package

    env_path = PROJECT_ROOT / ".env"
    user_config_path = PROJECT_ROOT / "config" / "user_config.json"
    backups = {
        env_path: env_path.read_bytes() if env_path.exists() else None,
        user_config_path: user_config_path.read_bytes() if user_config_path.exists() else None,
    }
    created_files = [
        PROJECT_ROOT / "data" / "runtime_friend_release_test.db",
        PROJECT_ROOT / "logs" / "runtime_friend_release_test.log",
        PROJECT_ROOT / ".venv" / "friend_release_marker.txt",
        PROJECT_ROOT / "agents" / "__pycache__" / "cached_friend_release.pyc",
    ]
    try:
        env_path.write_text("OPENAI_API_KEY=secret", encoding="utf-8")
        (PROJECT_ROOT / "config").mkdir(exist_ok=True)
        user_config_path.write_text(
            '{"openai_api_key": "secret"}', encoding="utf-8"
        )
        (PROJECT_ROOT / "data").mkdir(exist_ok=True)
        (PROJECT_ROOT / "data" / "runtime_friend_release_test.db").write_text("db", encoding="utf-8")
        (PROJECT_ROOT / "logs").mkdir(exist_ok=True)
        (PROJECT_ROOT / "logs" / "runtime_friend_release_test.log").write_text("log", encoding="utf-8")
        (PROJECT_ROOT / ".venv").mkdir(exist_ok=True)
        (PROJECT_ROOT / ".venv" / "friend_release_marker.txt").write_text("venv", encoding="utf-8")
        pycache = PROJECT_ROOT / "agents" / "__pycache__"
        pycache.mkdir(exist_ok=True)
        (pycache / "cached_friend_release.pyc").write_bytes(b"cache")

        zip_path = build_package(output_path=tmp_path / "LiteratureAgent_Windows.zip")
    finally:
        for path in created_files:
            if path.exists():
                path.unlink()
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert ".env" not in names
    assert "config/user_config.json" not in names
    assert "data/runtime_friend_release_test.db" not in names
    assert "logs/runtime_friend_release_test.log" not in names
    assert ".venv/friend_release_marker.txt" not in names
    assert "agents/__pycache__/cached_friend_release.pyc" not in names
    assert "app.py" in names
    assert "setup.bat" in names
    assert "config/user_config.example.json" in names
    assert "packaging/check_release.py" in names
