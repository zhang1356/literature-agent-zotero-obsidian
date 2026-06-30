from pydantic import BaseModel, Field


class Paper(BaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    abstract: str | None = None
    doi: str | None = None
    url: str | None = None
    source: str
    venue: str | None = None
    citation_count: int | None = None
    relevance_score: float | None = None
    novelty_score: float | None = None
    method_score: float | None = None
    reason: str | None = None
    tags: list[str] = Field(default_factory=list)
    data_source: str = "unknown"
    analysis_source: str = "none"


class SavedPaper(Paper):
    id: int
    zotero_key: str | None = None
    obsidian_path: str | None = None
    created_at: str
