import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Paper
from services.sync_service import SyncService


class FakeZoteroConnector:
    def __init__(self):
        self.added = []

    def create_collection(self, name):
        return "COLLECTION1"

    def add_paper_item(self, paper, collection_key=None):
        self.added.append((paper.title, collection_key))
        return f"KEY{len(self.added)}"


class FakeObsidianConnector:
    def __init__(self):
        self.notes = []

    def write_note(self, title, content):
        self.notes.append((title, content))
        return f"/vault/{title}.md"


def test_sync_service_skips_duplicate_papers(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_DATABASE_PATH", str(tmp_path / "test.db"))
    import config
    import database

    importlib.reload(config)
    database = importlib.reload(database)
    database.init_db()

    paper = Paper(
        title="Duplicate Paper",
        authors=["Grace Hopper"],
        year=2025,
        abstract="This is relevant.",
        doi="10.5555/duplicate",
        url="https://example.com/duplicate",
        source="mock",
        venue=None,
        relevance_score=90,
        tags=["duplicate"],
    )
    zotero = FakeZoteroConnector()
    obsidian = FakeObsidianConnector()
    service = SyncService(
        zotero_connector=zotero,
        obsidian_connector=obsidian,
        database_module=database,
    )

    first_result = service.save_selected_papers([paper], "AI Literature Agent")
    second_result = service.save_selected_papers([paper], "AI Literature Agent")

    assert first_result[0]["status"] == "success"
    assert second_result[0]["status"] == "skipped"
    assert len(zotero.added) == 1
    assert len(obsidian.notes) == 1


def test_missing_zotero_configuration_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("ZOTERO_LIBRARY_ID", raising=False)
    monkeypatch.delenv("ZOTERO_API_KEY", raising=False)
    import config
    import database

    importlib.reload(config)
    database = importlib.reload(database)
    database.init_db()

    service = SyncService(database_module=database, auto_connect=True)
    paper = Paper(
        title="No Zotero Config Paper",
        authors=[],
        year=2025,
        abstract="No crash expected.",
        doi=None,
        url=None,
        source="mock",
        venue=None,
        tags=[],
    )

    result = service.save_selected_papers([paper], "AI Literature Agent")

    assert result[0]["status"] == "failed"
    assert "未配置 Zotero 或 Obsidian" in result[0]["message"]
