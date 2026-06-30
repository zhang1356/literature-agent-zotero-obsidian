import json
import re
from collections import Counter

import httpx

from config import settings
from logger import get_logger
from models import Paper


logger = get_logger(__name__)


class RankAgent:
    def rank(self, papers: list[Paper], query: str) -> list[Paper]:
        ranked: list[Paper] = []
        for paper in papers:
            if settings.has_openai:
                ranked.append(self._rank_with_llm_or_fallback(paper, query))
            else:
                logger.warning("未配置模型 API Key，使用启发式评分：title=%s", paper.title)
                ranked.append(self._heuristic_rank(paper, query))
        return sorted(ranked, key=lambda p: p.relevance_score or 0, reverse=True)

    def _rank_with_llm_or_fallback(self, paper: Paper, query: str) -> Paper:
        try:
            result = self._call_openai_compatible_api(paper, query)
            result["analysis_source"] = "llm"
            return self._copy_paper(paper, result)
        except Exception as exc:
            logger.exception("模型评分失败，使用启发式评分：title=%s; error=%s", paper.title, exc)
            return self._heuristic_rank(paper, query)

    def _call_openai_compatible_api(self, paper: Paper, query: str) -> dict:
        base_url = settings.openai_base_url.strip() or "https://api.openai.com/v1"
        endpoint = base_url.rstrip("/") + "/chat/completions"
        prompt = (
            "你是文献检索智能体。请根据用户研究主题评估论文价值。"
            "只输出 JSON，不要输出 Markdown。字段必须为："
            '{"relevance_score": 88, "novelty_score": 75, '
            '"method_score": 80, "reason": "该论文与用户主题高度相关，因为……", '
            '"tags": ["RAG", "Multimodal", "Survey"]}\n\n'
            f"用户主题：{query}\n"
            f"标题：{paper.title}\n"
            f"作者：{', '.join(paper.authors)}\n"
            f"年份：{paper.year}\n"
            f"来源：{paper.source}\n"
            f"摘要：{paper.abstract or ''}"
        )
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": "你只输出可解析的 JSON 对象。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(self._strip_code_fence(content))
        return self._coerce_score_payload(parsed)

    def _heuristic_rank(self, paper: Paper, query: str) -> Paper:
        query_terms = self._terms(query)
        text_terms = self._terms(f"{paper.title} {paper.abstract or ''}")
        counts = Counter(text_terms)
        hit_count = sum(counts[term] for term in query_terms)
        coverage = len({term for term in query_terms if term in counts})

        relevance = min(70, hit_count * 12 + coverage * 10)
        if paper.year:
            relevance += max(0, min(12, paper.year - 2020))
        if paper.doi:
            relevance += 5
        if paper.abstract:
            relevance += 8
        relevance = max(30, min(100, relevance))

        novelty = 60
        if paper.year:
            novelty += max(0, min(25, (paper.year - 2020) * 4))
        method = 65
        if re.search(r"method|framework|model|approach|pipeline|算法|方法", paper.abstract or "", re.I):
            method += 15

        tags = self._make_tags(query, paper)
        if "heuristic-score" not in tags:
            tags.append("heuristic-score")
        reason = "标题或摘要与检索主题存在关键词匹配，且年份、摘要和 DOI 信息提升了可信度。"
        if coverage == 0:
            reason = "该论文与主题存在间接相关性，建议作为候选文献进一步人工筛选。"

        return self._copy_paper(
            paper,
            {
                "relevance_score": float(round(relevance, 2)),
                "novelty_score": float(min(100, novelty)),
                "method_score": float(min(100, method)),
                "reason": reason,
                "tags": tags,
                "analysis_source": "heuristic",
            },
        )

    @staticmethod
    def analysis_notice(papers: list[Paper]) -> str:
        if any(paper.analysis_source == "heuristic" for paper in papers):
            return "⚠️ 模型评分失败，已使用启发式评分，结果仅供参考。"
        return ""

    @staticmethod
    def _terms(text: str) -> list[str]:
        return [term for term in re.split(r"[\W_]+", text.lower()) if len(term) > 1]

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        content = content.strip()
        content = re.sub(r"^```json\s*", "", content, flags=re.I)
        content = re.sub(r"^```\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return content.strip()

    @staticmethod
    def _coerce_score_payload(payload: dict) -> dict:
        return {
            "relevance_score": float(payload.get("relevance_score", 0)),
            "novelty_score": float(payload.get("novelty_score", 0)),
            "method_score": float(payload.get("method_score", 0)),
            "reason": str(payload.get("reason", "")),
            "tags": [str(tag) for tag in payload.get("tags", [])][:5],
        }

    def _make_tags(self, query: str, paper: Paper) -> list[str]:
        tags = []
        for term in self._terms(query):
            if term not in tags:
                tags.append(term)
        for tag in paper.tags:
            if tag and tag not in tags:
                tags.append(tag)
        if paper.data_source == "mock" and "mock-data" not in tags:
            tags.append("mock-data")
        if paper.analysis_source == "heuristic" and "heuristic-score" not in tags:
            tags.append("heuristic-score")
        if paper.source and paper.source not in tags:
            tags.append(paper.source)
        return tags[:8] or ["literature"]

    @staticmethod
    def _copy_paper(paper: Paper, updates: dict) -> Paper:
        if hasattr(paper, "model_copy"):
            return paper.model_copy(update=updates)
        return paper.copy(update=updates)
