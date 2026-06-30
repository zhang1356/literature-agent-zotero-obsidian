import re
from pathlib import Path

from logger import get_logger


logger = get_logger(__name__)


class ObsidianConnector:
    def __init__(self, vault_path: str, literature_folder: str):
        self.vault_path = Path(vault_path).expanduser()
        if not str(vault_path).strip():
            raise ValueError("Obsidian Vault Path 未配置")
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Obsidian Vault 路径不存在：{self.vault_path}")

        self.literature_dir = self.vault_path / literature_folder
        self.literature_dir.mkdir(parents=True, exist_ok=True)

    def safe_filename(self, title: str) -> str:
        filename = re.sub(r'[<>:"/\\|?*]', "_", title).strip()
        filename = re.sub(r"\s+", " ", filename)
        filename = filename.rstrip(". ")
        return filename[:150] or "untitled"

    def write_note(self, title: str, content: str) -> str:
        if not self.literature_dir.exists():
            self.literature_dir.mkdir(parents=True, exist_ok=True)

        base_name = self.safe_filename(title)
        path = self.literature_dir / f"{base_name}.md"
        suffix = 1
        while path.exists():
            path = self.literature_dir / f"{base_name}-{suffix}.md"
            suffix += 1
        path.write_text(content, encoding="utf-8")
        return str(path)

    def note_exists(self, title: str) -> bool:
        base_name = self.safe_filename(title)
        return (self.literature_dir / f"{base_name}.md").exists()

    def list_literature_notes(self) -> list[dict]:
        if not self.literature_dir.exists():
            return []
        notes = []
        for path in sorted(self.literature_dir.glob("*.md")):
            notes.append({"filename": path.name, "path": str(path)})
        return notes

    def search_notes(self, keyword: str) -> list[dict]:
        keyword = keyword.strip()
        if not keyword:
            return []
        if not self.literature_dir.exists():
            return []

        results = []
        keyword_lower = keyword.lower()
        for path in sorted(self.literature_dir.glob("*.md")):
            try:
                content = path.read_text(encoding="utf-8")
            except Exception as exc:
                logger.warning("Obsidian 笔记读取失败：%s; %s", path, exc)
                continue

            searchable = f"{path.stem}\n{content}".lower()
            index = searchable.find(keyword_lower)
            if index == -1:
                continue
            snippet = self._snippet(content, keyword_lower)
            results.append(
                {"filename": path.name, "path": str(path), "snippet": snippet}
            )
        return results

    @staticmethod
    def _snippet(content: str, keyword_lower: str, radius: int = 60) -> str:
        content_lower = content.lower()
        index = content_lower.find(keyword_lower)
        if index == -1:
            return content[: radius * 2].strip()
        start = max(0, index - radius)
        end = min(len(content), index + len(keyword_lower) + radius)
        return content[start:end].replace("\n", " ").strip()
