import importlib
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.note_agent import NoteAgent
from agents.rank_agent import RankAgent
from agents.search_agent import SearchAgent
from config import Settings
from models import Paper
from services.connection_tests import (
    test_obsidian_path as check_obsidian_path,
    test_zotero_connection as check_zotero_connection,
)


def test_default_start_year_is_2026():
    import config

    assert config.DEFAULT_START_YEAR == 2026
    assert config.DEFAULT_VALUES["default_start_year"] == 2026
    assert config.Settings().default_start_year == 2026


def test_user_config_can_override_start_year(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "user_config.json").write_text(
        '{"default_start_year": 2027}',
        encoding="utf-8",
    )

    import config

    config = importlib.reload(config)

    assert config.get_settings().default_start_year == 2027


def test_arxiv_failure_returns_mock_papers_with_source_and_warning(monkeypatch):
    agent = SearchAgent()

    def fail(*args, **kwargs):
        raise RuntimeError("arXiv unavailable")

    monkeypatch.setattr(agent, "arxiv_search", fail)

    papers = agent.search("rag", year_from=2026, max_results=2)

    assert len(papers) == 2
    assert all(paper.data_source == "mock" for paper in papers)
    assert all(paper.source == "mock" for paper in papers)
    assert all(paper.year >= 2026 for paper in papers if paper.year)
    assert all("mock-data" in paper.tags for paper in papers)
    assert "mock 示例数据" in agent.source_notice(papers)


def test_heuristic_rank_marks_analysis_source_when_no_api_key(monkeypatch):
    import config
    import agents.rank_agent as rank_agent_module

    monkeypatch.setattr(config, "settings", Settings(openai_api_key=""))
    monkeypatch.setattr(rank_agent_module, "settings", config.settings)
    paper = Paper(
        title="Retrieval augmented generation",
        abstract="A method and framework for retrieval augmented generation.",
        source="arxiv",
        data_source="arxiv",
        year=2026,
    )

    ranked = RankAgent().rank([paper], "retrieval augmented generation")

    assert ranked[0].analysis_source == "heuristic"
    assert "heuristic-score" in ranked[0].tags
    assert "启发式评分" in RankAgent.analysis_notice(ranked)


def test_obsidian_template_contains_research_card_sections():
    paper = Paper(
        title='A/B:C* Research "Card"',
        authors=["Ada Lovelace"],
        year=2026,
        abstract="This paper solves a research problem with a useful method.",
        doi=None,
        url="https://arxiv.org/abs/2601.00001",
        source="arxiv",
        data_source="arxiv",
        analysis_source="heuristic",
        relevance_score=86,
        tags=["paper"],
    )

    markdown = NoteAgent().generate_markdown(paper, zotero_key="ZT123")

    for section in [
        "## 基本信息",
        "## 一句话总结",
        "## 研究问题",
        "## 方法结构",
        "## 主要贡献",
        "## 实验设置",
        "## 局限性",
        "## 可改进方向",
        "## 可用于我项目的点",
        "## 阅读状态",
        "## 标签",
    ]:
        assert section in markdown
    assert "- 数据来源：arxiv" in markdown
    assert "- 分析来源：heuristic" in markdown
    assert "- Zotero Key：ZT123" in markdown
    assert "待补充" in markdown


@pytest.mark.parametrize(
    ("score", "expected_priority"),
    [(90, "high-priority"), (80, "medium-priority"), (50, "low-priority")],
)
def test_zotero_tag_generation_adds_priority_and_transparency_tags(
    score, expected_priority
):
    import connectors.zotero_connector as zotero_connector

    paper = Paper(
        title="Tagged Paper",
        source="mock",
        data_source="mock",
        analysis_source="heuristic",
        relevance_score=score,
        tags=["existing"],
    )

    tags = zotero_connector.build_zotero_tags(paper)

    assert {"paper", "ai-analyzed", "read-later", expected_priority}.issubset(tags)
    assert "mock-data" in tags
    assert "heuristic-score" in tags
    assert "existing" in tags


def test_missing_obsidian_path_has_clear_error_message():
    ok, message = check_obsidian_path("", "Literature Notes")

    assert ok is False
    assert "Obsidian" in message
    assert "路径" in message


def test_missing_zotero_config_has_clear_error_message():
    ok, message = check_zotero_connection(Settings())

    assert ok is False
    assert "Zotero" in message
    assert "API Key" in message
