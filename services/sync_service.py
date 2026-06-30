from agents.note_agent import NoteAgent
from agents.rank_agent import RankAgent
from agents.search_agent import SearchAgent
from config import settings
from connectors.obsidian_connector import ObsidianConnector
from connectors.zotero_connector import ZoteroConnector
from logger import get_logger
from models import Paper


logger = get_logger(__name__)


class SyncService:
    def __init__(
        self,
        search_agent: SearchAgent | None = None,
        rank_agent: RankAgent | None = None,
        note_agent: NoteAgent | None = None,
        zotero_connector: ZoteroConnector | None = None,
        obsidian_connector: ObsidianConnector | None = None,
        database_module=None,
        auto_connect: bool = True,
    ):
        import database

        self.search_agent = search_agent or SearchAgent()
        self.rank_agent = rank_agent or RankAgent()
        self.note_agent = note_agent or NoteAgent()
        self.database = database_module or database
        self.zotero = zotero_connector
        self.obsidian = obsidian_connector

        if auto_connect and self.zotero is None and settings.has_zotero:
            self.zotero = ZoteroConnector(
                settings.zotero_library_id,
                settings.zotero_library_type,
                settings.zotero_api_key,
            )
        if auto_connect and self.obsidian is None and settings.has_obsidian:
            self.obsidian = ObsidianConnector(
                settings.obsidian_vault_path,
                settings.obsidian_literature_folder,
            )

    def search_and_rank(
        self, query: str, year_from: int | None, max_results: int
    ) -> list[Paper]:
        logger.info("检索关键词：%s", query)
        papers = self.search_agent.search(query, year_from=year_from, max_results=max_results)
        return self.rank_agent.rank(papers, query)

    def save_selected_papers(
        self, papers: list[Paper], collection_name: str, year_from: int | None = None
    ) -> list[dict]:
        results: list[dict] = []
        collection_key: str | None = None

        if self.zotero:
            try:
                if (
                    collection_name == "AI Literature Agent"
                    and hasattr(self.zotero, "ensure_literature_agent_collection")
                ):
                    collection_key = self.zotero.ensure_literature_agent_collection(year_from)
                else:
                    collection_key = self.zotero.create_collection(collection_name)
            except Exception as exc:
                logger.exception("Zotero 创建 Collection 失败：%s", exc)
                collection_key = None

        for paper in papers:
            result = {
                "标题": paper.title,
                "Zotero": "跳过",
                "Obsidian": "跳过",
                "SQLite": "跳过",
                "Obsidian 文件路径": "",
                "Zotero Key": "",
                "错误原因": "",
            }

            if self.database.is_duplicate(paper.title, paper.doi):
                result["SQLite"] = "已存在"
                result["Zotero"] = "跳过"
                result["Obsidian"] = "跳过"
                result["错误原因"] = "SQLite 已存在，跳过重复导入。"
                result.update(self._legacy_result_fields("skipped", result["错误原因"]))
                results.append(result)
                continue

            zotero_key: str | None = None
            obsidian_path: str | None = None

            errors: list[str] = []
            if self.zotero:
                try:
                    zotero_key = self.zotero.add_paper_item(paper, collection_key)
                    result["Zotero"] = "成功"
                    result["Zotero Key"] = zotero_key or ""
                except Exception as exc:
                    logger.exception("Zotero 写入失败：%s; title=%s", exc, paper.title)
                    result["Zotero"] = "失败"
                    errors.append("Zotero 写入失败：请检查 API Key 是否开启写入权限。")
            else:
                errors.append("尚未配置 Zotero，已跳过 Zotero 同步。")

            if self.obsidian:
                try:
                    content = self.note_agent.generate_markdown(paper, zotero_key)
                    obsidian_path = self.obsidian.write_note(paper.title, content)
                    result["Obsidian"] = "成功"
                    result["Obsidian 文件路径"] = obsidian_path or ""
                except Exception as exc:
                    logger.exception("Obsidian 写入失败：%s; title=%s", exc, paper.title)
                    result["Obsidian"] = "失败"
                    errors.append("Obsidian 写入失败：请检查 Vault 路径是否正确。")
            else:
                errors.append("尚未配置 Obsidian，无法生成 Markdown 笔记。")

            if zotero_key or obsidian_path:
                try:
                    record_id = self.database.save_paper_record(
                        paper, zotero_key, obsidian_path
                    )
                    result["SQLite"] = "成功"
                    logger.info("保存成功的论文标题：%s; SQLite ID=%s", paper.title, record_id)
                except Exception as exc:
                    logger.exception("SQLite 保存失败：%s; title=%s", exc, paper.title)
                    result["SQLite"] = "失败"
                    errors.append("SQLite 保存失败，请查看日志。")
            else:
                result["SQLite"] = "跳过"
                if not self.zotero and not self.obsidian:
                    errors = ["未配置 Zotero 或 Obsidian，仅支持检索和评分。"]

            result["错误原因"] = "；".join(errors)
            status = "success" if result["SQLite"] == "成功" else "failed"
            if result["SQLite"] in {"跳过", "已存在"}:
                status = "skipped" if result["SQLite"] == "已存在" else "failed"
            result.update(
                self._legacy_result_fields(
                    status,
                    result["错误原因"] or "保存完成。",
                    zotero_key=zotero_key,
                    obsidian_path=obsidian_path,
                )
            )
            results.append(result)
        return results

    @staticmethod
    def _legacy_result_fields(
        status: str,
        message: str,
        zotero_key: str | None = None,
        obsidian_path: str | None = None,
    ) -> dict:
        return {
            "status": status,
            "message": message,
            "zotero_key": zotero_key,
            "obsidian_path": obsidian_path,
        }
