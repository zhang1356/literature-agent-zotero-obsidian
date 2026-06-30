import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import requests

from config import DEFAULT_START_YEAR
from logger import get_logger
from models import Paper


logger = get_logger(__name__)


class SearchAgent:
    def search(
        self, query: str, year_from: int | None = None, max_results: int = 10
    ) -> list[Paper]:
        year_from = year_from or DEFAULT_START_YEAR
        try:
            papers = self.arxiv_search(query, year_from=year_from, max_results=max_results)
            if papers:
                return self._filter_by_year(papers, year_from)[:max_results]
            logger.warning("arXiv 检索无结果，回退到 mock 示例数据：query=%s", query)
            return self.mock_search(query, year_from=year_from, max_results=max_results)
        except Exception as exc:
            logger.exception("arXiv 检索失败，回退到 mock 示例数据：query=%s; error=%s", query, exc)
            return self.mock_search(query, year_from=year_from, max_results=max_results)

    def arxiv_search(
        self, query: str, year_from: int | None = None, max_results: int = 10
    ) -> list[Paper]:
        encoded_query = quote_plus(f'all:"{query}"')
        url = (
            "https://export.arxiv.org/api/query"
            f"?search_query={encoded_query}&start=0&max_results={max_results}"
            "&sortBy=submittedDate&sortOrder=descending"
        )
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        papers: list[Paper] = []
        for entry in root.findall("atom:entry", ns):
            title = self._clean_text(entry.findtext("atom:title", default="", namespaces=ns))
            abstract = self._clean_text(
                entry.findtext("atom:summary", default="", namespaces=ns)
            )
            published = entry.findtext("atom:published", default="", namespaces=ns)
            year = self._extract_year(published)
            if year_from and year and year < year_from:
                continue
            authors = [
                self._clean_text(author.findtext("atom:name", default="", namespaces=ns))
                for author in entry.findall("atom:author", ns)
            ]
            doi = entry.findtext("arxiv:doi", default=None, namespaces=ns)
            papers.append(
                Paper(
                    title=title,
                    authors=[author for author in authors if author],
                    year=year,
                    abstract=abstract,
                    doi=doi,
                    url=entry.findtext("atom:id", default=None, namespaces=ns),
                    source="arxiv",
                    data_source="arxiv",
                    venue="arXiv",
                    citation_count=None,
                    tags=["arxiv"],
                )
            )
        return papers

    def mock_search(
        self, query: str, year_from: int | None = None, max_results: int = 3
    ) -> list[Paper]:
        base_year = max(year_from or 2024, 2024)
        papers = [
            Paper(
                title=f"{query} for Literature Discovery: A Practical Survey",
                authors=["Alice Chen", "Bo Wang"],
                year=base_year,
                abstract=(
                    f"This survey reviews recent methods related to {query}, "
                    "covering retrieval, ranking, evaluation, and deployment tradeoffs."
                ),
                doi="10.0000/mock-survey",
                url="https://example.org/mock-survey",
                source="mock",
                data_source="mock",
                analysis_source="mock",
                venue="Mock AI Review",
                citation_count=42,
                tags=["mock", "mock-data", "survey"],
            ),
            Paper(
                title=f"Efficient Retrieval-Augmented Methods for {query}",
                authors=["Carla Smith"],
                year=base_year + 1,
                abstract=(
                    f"The paper proposes a lightweight retrieval-augmented pipeline for {query} "
                    "with simple indexing and robust reranking."
                ),
                doi=None,
                url="https://example.org/mock-rag",
                source="mock",
                data_source="mock",
                analysis_source="mock",
                venue="MockConf",
                citation_count=12,
                tags=["mock", "mock-data", "retrieval"],
            ),
            Paper(
                title=f"Benchmarking Open Research Workflows with {query}",
                authors=["Diego Liu", "Eva Kumar"],
                year=base_year,
                abstract=(
                    f"This benchmark studies reproducible research workflows for {query} "
                    "and compares annotation quality across tools."
                ),
                doi=None,
                url="https://example.org/mock-benchmark",
                source="mock",
                data_source="mock",
                analysis_source="mock",
                venue="Mock Benchmarks",
                citation_count=5,
                tags=["mock", "mock-data", "benchmark"],
            ),
        ]
        return self._filter_by_year(papers, year_from)[:max_results]

    @staticmethod
    def source_notice(papers: list[Paper]) -> str:
        if any(paper.data_source == "mock" for paper in papers):
            return "⚠️ 当前结果来自 mock 示例数据，不是真实 arXiv 检索结果。"
        return ""

    @staticmethod
    def _filter_by_year(papers: list[Paper], year_from: int | None) -> list[Paper]:
        if not year_from:
            return papers
        return [paper for paper in papers if paper.year is None or paper.year >= year_from]

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    @staticmethod
    def _extract_year(value: str) -> int | None:
        match = re.match(r"(\d{4})", value or "")
        return int(match.group(1)) if match else None
