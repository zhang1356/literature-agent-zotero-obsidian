import importlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_no_zotero_no_obsidian_service_initializes(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ZOTERO_LIBRARY_ID", raising=False)
    monkeypatch.delenv("ZOTERO_API_KEY", raising=False)
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.setenv("APP_DATABASE_PATH", str(tmp_path / "data" / "test.db"))

    import config
    import services.sync_service as sync_service

    importlib.reload(config)
    sync_service = importlib.reload(sync_service)

    service = sync_service.SyncService(auto_connect=True)

    assert service.zotero is None
    assert service.obsidian is None


def test_theme_apply_theme_can_be_imported_and_called(monkeypatch):
    import ui.theme as theme

    calls = []
    monkeypatch.setattr(theme.st, "markdown", lambda body, unsafe_allow_html: calls.append((body, unsafe_allow_html)))

    theme.apply_theme()

    assert calls
    assert "background: #F7F1E8" in calls[0][0]
    assert calls[0][1] is True
