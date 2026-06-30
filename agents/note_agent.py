import json

from config import settings
from logger import get_logger
from models import Paper


logger = get_logger(__name__)


class NoteAgent:
    def generate_markdown(self, paper: Paper, zotero_key: str | None = None) -> str:
        summary = self._summary(paper)
        authors = ", ".join(paper.authors) if paper.authors else "待补充"
        year = paper.year or "待补充"
        source = paper.source or "待补充"
        data_source = paper.data_source or "unknown"
        analysis_source = paper.analysis_source or "none"
        priority = self._priority(paper)
        return f"""---
title: {json.dumps(paper.title, ensure_ascii=False)}
year: {paper.year or ""}
authors: {json.dumps(paper.authors, ensure_ascii=False)}
source: {json.dumps(paper.source, ensure_ascii=False)}
data_source: {json.dumps(data_source, ensure_ascii=False)}
analysis_source: {json.dumps(analysis_source, ensure_ascii=False)}
doi: {json.dumps(paper.doi or "", ensure_ascii=False)}
url: {json.dumps(paper.url or "", ensure_ascii=False)}
zotero_key: {json.dumps(zotero_key or "", ensure_ascii=False)}
score: {paper.relevance_score or 0}
tags: {json.dumps(paper.tags, ensure_ascii=False)}
status: unread
---

# {paper.title}

## 基本信息

- 年份：{year}
- 作者：{authors}
- 来源：{source}
- arXiv：{paper.url or "待补充"}
- DOI：{paper.doi or "待补充"}
- Zotero Key：{zotero_key or "待补充"}
- 数据来源：{data_source}
- 分析来源：{analysis_source}

## 一句话总结

{summary}

## 研究问题

{paper.reason or "待补充"}

## 方法结构

- 输入：待补充
- 核心模块：待补充
- 训练目标：待补充
- 输出：待补充

## 主要贡献

1. 待补充
2. 待补充
3. 待补充

## 实验设置

- 数据集：待补充
- Baseline：待补充
- 指标：待补充
- 主要结果：待补充

## 局限性

1. 待补充
2. 待补充
3. 待补充

## 可改进方向

1. 待补充
2. 待补充
3. 待补充

## 可用于我项目的点

- 可复现：待补充
- 可借鉴：可用于相关工作、方法对比或研究背景部分。
- 可改进：待补充
- 可写进相关工作：待补充

## 阅读状态

- 状态：待阅读
- 优先级：{priority}
- 是否已加入 Zotero：{"是" if zotero_key else "否"}
- 是否已完成复现：否

## 摘要

{paper.abstract or "待补充"}

## 相关性判断

- 评分：{paper.relevance_score or 0}
- 评分来源：{self._analysis_source_label(analysis_source)}
- 理由：{paper.reason or "待补充"}

## 标签

#paper #zotero #obsidian #待阅读
"""

    def _summary(self, paper: Paper) -> str:
        if settings.has_openai:
            try:
                return self._summary_with_llm(paper)
            except Exception as exc:
                logger.exception("生成一句话总结失败，回退到摘要截断：title=%s; error=%s", paper.title, exc)
        abstract = paper.abstract or ""
        return abstract[:200] if abstract else "待补充"

    def _summary_with_llm(self, paper: Paper) -> str:
        import httpx

        base_url = settings.openai_base_url.strip() or "https://api.openai.com/v1"
        endpoint = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是学术助手，用一句中文总结论文价值，不超过 60 字。",
                },
                {
                    "role": "user",
                    "content": f"标题：{paper.title}\n摘要：{paper.abstract or ''}",
                },
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
        return response.json()["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _analysis_source_label(value: str) -> str:
        labels = {
            "llm": "LLM",
            "heuristic": "启发式规则",
            "mock": "mock 示例",
            "none": "未评分",
        }
        return labels.get(value, value or "未评分")

    @staticmethod
    def _priority(paper: Paper) -> str:
        score = paper.relevance_score or 0
        if score >= 85:
            return "高"
        if score >= 70:
            return "中"
        if score > 0:
            return "低"
        return "待补充"
