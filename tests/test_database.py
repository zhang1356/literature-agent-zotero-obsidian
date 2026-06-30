import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Paper


def reload_database_with_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_DATABASE_PATH", str(tmp_path / "test.db"))
    import config
    import database

    importlib.reload(config)
    return importlib.reload(database)


def test_init_db_creates_papers_table(monkeypatch, tmp_path):
    database = reload_database_with_path(monkeypatch, tmp_path)

    database.init_db()

    saved = database.list_saved_papers()
    assert saved == []


def test_doi_deduplication(monkeypatch, tmp_path):
    database = reload_database_with_path(monkeypatch, tmp_path)
    database.init_db()
    paper = Paper(
        title="A Useful Paper",
        authors=["Ada Lovelace"],
        year=2024,
        abstract="Abstract",
        doi="10.1234/example",
        url="https://example.com",
        source="mock",
        venue="TestConf",
        tags=["test"],
    )

    assert database.is_duplicate(paper.title, paper.doi) is False
    database.save_paper_record(paper, "ABC123", "/vault/A Useful Paper.md")

    assert database.is_duplicate("Different Title", "10.1234/example") is True


def test_title_normalization_deduplicates_without_doi(monkeypatch, tmp_path):
    database = reload_database_with_path(monkeypatch, tmp_path)
    database.init_db()
    paper = Paper(
        title="An   Efficient, Method!",
        authors=[],
        year=None,
        abstract=None,
        doi=None,
        url=None,
        source="mock",
        venue=None,
        tags=[],
    )

    database.save_paper_record(paper, "XYZ789", "/vault/An Efficient Method.md")

    assert database.normalize_title("An Efficient Method") == "an efficient method"
    assert database.is_duplicate("an efficient method", None) is True


def test_fuzzy_title_matching_deduplicates_similar_titles(monkeypatch, tmp_path):
    database = reload_database_with_path(monkeypatch, tmp_path)
    database.init_db()
    paper = Paper(
        title="Retrieval-Augmented Generation: A Survey of Methods",
        authors=[],
        year=2025,
        abstract=None,
        doi=None,
        url=None,
        source="mock",
        venue=None,
        tags=[],
    )

    database.save_paper_record(paper, None, None)

    assert database.is_duplicate(
        "retrieval augmented generation - a survey of method", None
    ) is True


def test_list_saved_papers_reads_sqlite_records(monkeypatch, tmp_path):
    database = reload_database_with_path(monkeypatch, tmp_path)
    database.init_db()
    paper = Paper(
        title="Readable Saved Paper",
        authors=["Ada Lovelace"],
        year=2026,
        abstract="Saved abstract",
        doi="10.9999/readable",
        url="https://example.com/readable",
        source="mock",
        venue=None,
        relevance_score=91,
        tags=["saved", "sqlite"],
    )

    database.save_paper_record(paper, "ZT123", "D:/vault/Literature Notes/Readable.md")

    saved = database.list_saved_papers()
    assert len(saved) == 1
    assert saved[0].title == "Readable Saved Paper"
    assert saved[0].doi == "10.9999/readable"
    assert saved[0].zotero_key == "ZT123"
    assert saved[0].obsidian_path.endswith("Readable.md")
