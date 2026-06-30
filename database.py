import json
import re
import sqlite3
import csv
import io
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings
from logger import get_logger
from models import Paper, SavedPaper


logger = get_logger(__name__)
FUZZY_TITLE_THRESHOLD = 0.92


def get_connection() -> sqlite3.Connection:
    db_path = Path(settings.app_database_path)
    if db_path.parent and str(db_path.parent) != ".":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db() -> None:
    try:
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    title_norm TEXT,
                    doi TEXT,
                    url TEXT,
                    year INTEGER,
                    abstract TEXT,
                    source TEXT,
                    data_source TEXT,
                    analysis_source TEXT,
                    zotero_key TEXT,
                    obsidian_path TEXT,
                    relevance_score REAL,
                    novelty_score REAL,
                    method_score REAL,
                    tags TEXT,
                    created_at TEXT
                )
                """
            )
            _ensure_column(conn, "papers", "data_source", "TEXT")
            _ensure_column(conn, "papers", "analysis_source", "TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_papers_title_norm ON papers(title_norm)"
            )
    except Exception:
        logger.exception("数据库初始化失败")
        raise


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl_type: str) -> None:
    existing = {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")


def normalize_title(title: str) -> str:
    normalized = re.sub(r"[:：\-–—_]+", " ", title.lower(), flags=re.UNICODE)
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def is_duplicate(title: str, doi: str | None) -> bool:
    init_db()
    try:
        with get_connection() as conn:
            if doi:
                row = conn.execute(
                    "SELECT id FROM papers WHERE lower(doi) = lower(?) LIMIT 1",
                    (doi.strip(),),
                ).fetchone()
                if row:
                    return True

            title_norm = normalize_title(title)
            row = conn.execute(
                "SELECT id FROM papers WHERE title_norm = ? LIMIT 1", (title_norm,)
            ).fetchone()
            if row:
                return True

            rows = conn.execute(
                "SELECT title_norm FROM papers WHERE title_norm IS NOT NULL"
            ).fetchall()
            for (saved_title_norm,) in rows:
                if not saved_title_norm:
                    continue
                score = SequenceMatcher(None, title_norm, saved_title_norm).ratio()
                if score > FUZZY_TITLE_THRESHOLD:
                    return True
            return False
    except Exception:
        logger.exception("数据库去重检查失败")
        raise


def save_paper_record(
    paper: Paper, zotero_key: str | None, obsidian_path: str | None
) -> int:
    init_db()
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO papers (
                    title, title_norm, doi, url, year, abstract, source,
                    data_source, analysis_source,
                    zotero_key, obsidian_path, relevance_score, novelty_score,
                    method_score, tags, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper.title,
                    normalize_title(paper.title),
                    paper.doi,
                    paper.url,
                    paper.year,
                    paper.abstract,
                    paper.source,
                    paper.data_source,
                    paper.analysis_source,
                    zotero_key,
                    obsidian_path,
                    paper.relevance_score,
                    paper.novelty_score,
                    paper.method_score,
                    json.dumps(paper.tags, ensure_ascii=False),
                    created_at,
                ),
            )
            return int(cursor.lastrowid)
    except Exception:
        logger.exception("数据库保存论文记录失败：%s", paper.title)
        raise


def list_saved_papers() -> list[SavedPaper]:
    init_db()
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM papers ORDER BY created_at DESC").fetchall()
    except Exception:
        logger.exception("数据库读取已保存论文失败")
        raise

    saved: list[SavedPaper] = []
    for row in rows:
        data: dict[str, Any] = dict(row)
        tags = json.loads(data.get("tags") or "[]")
        saved.append(
            SavedPaper(
                id=data["id"],
                title=data.get("title") or "",
                authors=[],
                year=data.get("year"),
                abstract=data.get("abstract"),
                doi=data.get("doi"),
                url=data.get("url"),
                source=data.get("source") or "",
                data_source=data.get("data_source") or data.get("source") or "unknown",
                analysis_source=data.get("analysis_source") or "none",
                venue=None,
                relevance_score=data.get("relevance_score"),
                novelty_score=data.get("novelty_score"),
                method_score=data.get("method_score"),
                tags=tags,
                zotero_key=data.get("zotero_key"),
                obsidian_path=data.get("obsidian_path"),
                created_at=data.get("created_at") or "",
            )
        )
    return saved


def search_saved_papers(
    query: str = "", year: int | None = None, papers: list[SavedPaper] | None = None
) -> list[SavedPaper]:
    source = papers if papers is not None else list_saved_papers()
    keyword = query.strip().lower()
    filtered: list[SavedPaper] = []
    for paper in source:
        if year is not None and paper.year != year:
            continue
        if keyword:
            searchable = " ".join(
                [
                    paper.title or "",
                    paper.doi or "",
                    " ".join(paper.tags),
                ]
            ).lower()
            if keyword not in searchable:
                continue
        filtered.append(paper)
    return filtered


def saved_papers_to_csv(papers: list[SavedPaper]) -> str:
    output = io.StringIO()
    fieldnames = [
        "标题",
        "年份",
        "DOI",
        "标签",
        "Zotero Key",
        "Obsidian 路径",
        "保存时间",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for paper in papers:
        writer.writerow(
            {
                "标题": paper.title,
                "年份": paper.year or "",
                "DOI": paper.doi or "",
                "标签": ", ".join(paper.tags),
                "Zotero Key": paper.zotero_key or "",
                "Obsidian 路径": paper.obsidian_path or "",
                "保存时间": paper.created_at,
            }
        )
    return output.getvalue()
