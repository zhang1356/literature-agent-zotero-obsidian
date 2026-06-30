import importlib
import importlib.util
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Settings
from models import Paper
from services.connection_tests import (
    test_model_api as check_model_api,
    test_obsidian_path as check_obsidian_path,
    test_zotero_connection as check_zotero_connection,
)
from services.sync_service import SyncService


def test_obsidian_path_detection_writes_and_cleans_temp_file(tmp_path):
    ok, message = check_obsidian_path(str(tmp_path), "Literature Notes")

    assert ok is True
    assert message == "Obsidian 路径可用。"
    literature_dir = tmp_path / "AI-Literature-Agent" / "Inbox"
    assert literature_dir.exists()
    assert (tmp_path / "AI-Literature-Agent" / "Analyzed").exists()
    assert (tmp_path / "AI-Literature-Agent" / "Logs").exists()
    assert list(literature_dir.glob(".literature_agent_test_*.tmp")) == []


def test_obsidian_path_detection_rejects_missing_path(tmp_path):
    ok, message = check_obsidian_path(str(tmp_path / "missing"), "Literature Notes")

    assert ok is False
    assert "路径不存在" in message


def test_no_configuration_checks_return_friendly_messages():
    settings = Settings()

    zotero_ok, zotero_message = check_zotero_connection(settings)
    model_ok, model_message = check_model_api(settings)

    assert zotero_ok is False
    assert "请先填写 Zotero" in zotero_message
    assert model_ok is False
    assert "请先填写 API Key" in model_message


def test_zotero_unconfigured_save_flow_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_DATABASE_PATH", str(tmp_path / "test.db"))
    import config
    import database

    importlib.reload(config)
    database = importlib.reload(database)
    database.init_db()

    service = SyncService(database_module=database, auto_connect=False)
    paper = Paper(title="Unconfigured Paper", source="mock")

    result = service.save_selected_papers([paper], "AI Literature Agent")

    assert result[0]["Zotero"] == "跳过"
    assert result[0]["Obsidian"] == "跳过"
    assert result[0]["SQLite"] == "跳过"
    assert "未配置 Zotero 或 Obsidian" in result[0]["错误原因"]


def test_saved_papers_search_and_csv_export(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_DATABASE_PATH", str(tmp_path / "test.db"))
    import config
    import database

    importlib.reload(config)
    database = importlib.reload(database)
    database.init_db()

    paper = Paper(
        title="Graph Neural Network Review",
        year=2025,
        doi="10.1000/gnn",
        source="mock",
        tags=["graph", "review"],
    )
    database.save_paper_record(paper, "ZTKEY", str(tmp_path / "note.md"))

    results = database.search_saved_papers("graph", 2025)
    csv_text = database.saved_papers_to_csv(results)

    assert len(results) == 1
    assert results[0].title == "Graph Neural Network Review"
    assert "Graph Neural Network Review" in csv_text
    assert "ZTKEY" in csv_text


def test_check_release_identifies_sensitive_files(tmp_path):
    module_path = PROJECT_ROOT / "packaging" / "check_release.py"
    spec = importlib.util.spec_from_file_location("check_release", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(".env", "OPENAI_API_KEY=sk-real-secret")
        archive.writestr("app.py", "print('ok')")

    ok, errors, _ = module.check_zip(zip_path)

    assert ok is False
    assert any(".env" in error for error in errors)
