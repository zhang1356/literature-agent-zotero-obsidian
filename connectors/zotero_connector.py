from models import Paper


def build_zotero_tags(paper: Paper) -> set[str]:
    tags = {tag.strip() for tag in paper.tags if tag and tag.strip()}
    tags.update({"paper", "ai-analyzed", "read-later"})

    score = paper.relevance_score or 0
    if score >= 85:
        tags.add("high-priority")
    elif score >= 70:
        tags.add("medium-priority")
    else:
        tags.add("low-priority")

    if paper.data_source == "mock":
        tags.add("mock-data")
    if paper.analysis_source == "heuristic":
        tags.add("heuristic-score")
    return tags


class ZoteroConnector:
    def __init__(self, library_id: str, library_type: str, api_key: str):
        if not library_id or not api_key:
            raise ValueError("Zotero Library ID 或 API Key 未配置")
        try:
            from pyzotero import zotero
        except Exception as exc:
            raise RuntimeError("pyzotero 未安装，请先运行 pip install -r requirements.txt") from exc

        self.zot = zotero.Zotero(library_id, library_type, api_key)

    def get_recent_items(self, limit: int = 10):
        try:
            return self.zot.top(limit=limit, sort="dateAdded", direction="desc")
        except Exception as exc:
            raise RuntimeError(f"读取 Zotero 最近条目失败：{exc}") from exc

    def search_items(self, query: str, limit: int = 20):
        try:
            return self.zot.items(q=query, limit=limit)
        except Exception as exc:
            raise RuntimeError(f"搜索 Zotero 条目失败：{exc}") from exc

    def list_collections(self):
        try:
            return self.zot.collections()
        except Exception as exc:
            raise RuntimeError(f"读取 Zotero Collection 失败：{exc}") from exc

    def get_items_by_collection(self, collection_key: str, limit: int = 50):
        try:
            return self.zot.collection_items(collection_key, limit=limit)
        except Exception as exc:
            raise RuntimeError(f"读取 Zotero Collection 条目失败：{exc}") from exc

    def create_collection(self, name: str, parent_key: str | None = None) -> str:
        try:
            existing = self.zot.collections(q=name)
            for collection in existing:
                data = collection.get("data", {})
                if data.get("name") == name and data.get("parentCollection") == parent_key:
                    return collection["key"]

            payload = [{"name": name}]
            if parent_key:
                payload[0]["parentCollection"] = parent_key
            response = self.zot.create_collections(payload)
            successful = response.get("successful", {})
            if successful:
                first = next(iter(successful.values()))
                return first["key"]
            raise RuntimeError(str(response))
        except Exception as exc:
            raise RuntimeError(f"创建 Zotero Collection 失败：{exc}") from exc

    def ensure_literature_agent_collection(self, year_from: int | None = None) -> str:
        parent_key = self.create_collection("AI Literature Agent")
        if year_from and year_from >= 2026:
            return self.create_collection("2026+", parent_key=parent_key)
        return parent_key

    def add_paper_item(
        self, paper: Paper, collection_key: str | None = None
    ) -> str:
        try:
            item_type = "journalArticle" if self._has_journal_fields(paper) else "webpage"
            template = self.zot.item_template(item_type)
            template["title"] = paper.title
            template["abstractNote"] = paper.abstract or ""
            template["url"] = paper.url or ""
            if item_type == "journalArticle":
                template["DOI"] = paper.doi or ""
                template["publicationTitle"] = paper.venue or paper.source
            if paper.year:
                template["date"] = str(paper.year)

            template["creators"] = [
                self._creator_from_name(author) for author in paper.authors if author.strip()
            ]
            template["tags"] = [{"tag": tag} for tag in sorted(build_zotero_tags(paper))]
            if collection_key:
                template["collections"] = [collection_key]

            response = self.zot.create_items([template])
            successful = response.get("successful", {})
            if successful:
                first = next(iter(successful.values()))
                return first["key"]
            raise RuntimeError(str(response))
        except Exception as exc:
            raise RuntimeError(f"写入 Zotero 条目失败：{exc}") from exc

    @staticmethod
    def _has_journal_fields(paper: Paper) -> bool:
        return bool(paper.title and (paper.doi or paper.venue or paper.year))

    @staticmethod
    def _creator_from_name(name: str) -> dict:
        parts = name.strip().split()
        if len(parts) <= 1:
            return {"creatorType": "author", "name": name.strip()}
        return {
            "creatorType": "author",
            "firstName": " ".join(parts[:-1]),
            "lastName": parts[-1],
        }
