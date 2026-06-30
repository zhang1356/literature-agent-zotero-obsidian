import importlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.rank_agent import RankAgent
from connectors.obsidian_connector import ObsidianConnector
from models import Paper
from services.sync_service import SyncService


def test_missing_user_config_does_not_crash_and_reports_guidance(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "user_config.example.json").write_text("{}", encoding="utf-8")

    import config

    config = importlib.reload(config)
    result = config.validate_user_config()

    assert result["ok"] is False
    assert result["config_path"].endswith("config/user_config.json")
    assert "尚未检测到 config/user_config.json" in " ".join(result["warnings"])
    assert config.get_settings().openai_model == "qwen-plus"


def test_user_config_missing_fields_are_listed(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "user_config.example.json").write_text("{}", encoding="utf-8")
    (config_dir / "user_config.json").write_text(
        '{"openai_api_key": "sk-test"}',
        encoding="utf-8",
    )

    import config

    config = importlib.reload(config)
    result = config.validate_user_config()

    assert result["ok"] is False
    assert "openai_base_url" in result["missing_fields"]
    assert "zotero_library_id" in result["missing_fields"]
    assert "obsidian_vault_path" in result["missing_fields"]


def test_obsidian_missing_paths_return_clear_errors(tmp_path):
    from services.local_status import check_obsidian_path_status

    empty_status = check_obsidian_path_status("")
    missing_status = check_obsidian_path_status(str(tmp_path / "missing"))

    assert empty_status["ok"] is False
    assert "未配置" in empty_status["message"]
    assert missing_status["ok"] is False
    assert "不存在" in missing_status["message"]


def test_obsidian_connector_creates_local_folders_and_uses_timestamp_on_duplicate(tmp_path):
    connector = ObsidianConnector(str(tmp_path), "Literature Notes")

    first = Path(connector.write_note("A Paper", "old"))
    second = Path(connector.write_note("A Paper", "new"))

    assert (tmp_path / "AI-Literature-Agent" / "Inbox").exists()
    assert (tmp_path / "AI-Literature-Agent" / "Analyzed").exists()
    assert (tmp_path / "AI-Literature-Agent" / "Logs").exists()
    assert first.parent.name == "Inbox"
    assert second.parent.name == "Inbox"
    assert first.read_text(encoding="utf-8") == "old"
    assert second.read_text(encoding="utf-8") == "new"
    assert first != second
    assert second.stem.startswith("A Paper-")


class LocalOnlyDatabase:
    def __init__(self):
        self.saved = []

    def is_duplicate(self, title, doi):
        return False

    def save_paper_record(self, paper, zotero_key, obsidian_path):
        self.saved.append((paper, zotero_key, obsidian_path))
        return len(self.saved)


def test_missing_zotero_does_not_block_obsidian_write(tmp_path):
    connector = ObsidianConnector(str(tmp_path), "Literature Notes")
    service = SyncService(
        obsidian_connector=connector,
        zotero_connector=None,
        database_module=LocalOnlyDatabase(),
        auto_connect=False,
    )
    paper = Paper(title="Local Note Only", source="mock", data_source="mock")

    result = service.save_selected_papers([paper], "AI Literature Agent")

    assert result[0]["Obsidian"] == "成功"
    assert result[0]["Zotero"] == "跳过"
    assert "尚未配置 Zotero" in result[0]["错误原因"]
    assert Path(result[0]["Obsidian 文件路径"]).exists()


def test_missing_api_key_uses_heuristic_scoring(monkeypatch):
    import config
    import agents.rank_agent as rank_agent_module

    monkeypatch.setattr(config, "settings", config.Settings(openai_api_key=""))
    monkeypatch.setattr(rank_agent_module, "settings", config.settings)
    paper = Paper(title="retrieval model", abstract="A method for retrieval.", source="arxiv")

    ranked = RankAgent().rank([paper], "retrieval")

    assert ranked[0].analysis_source == "heuristic"
    assert "heuristic-score" in ranked[0].tags


def test_local_environment_check_returns_structured_result(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "user_config.example.json").write_text("{}", encoding="utf-8")

    import config
    from services.local_status import check_local_environment

    config = importlib.reload(config)
    result = check_local_environment(config.Settings())

    assert set(["ok", "checks", "warnings", "config"]).issubset(result)
    assert (tmp_path / "data").exists()
    assert (tmp_path / "logs").exists()
    assert "python" in result["checks"]
    assert "dependencies" in result["checks"]


def test_start_app_bat_exists():
    assert Path("start_app.bat").exists()
