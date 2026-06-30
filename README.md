# literature-agent-zotero-obsidian

本项目是一个本地运行的文献检索智能体 MVP。它使用 Streamlit 提供界面，支持输入研究主题、检索候选论文、评分排序、勾选高价值论文，并将结果同步到 Zotero 与 Obsidian Markdown 笔记，同时用 SQLite 记录同步历史以避免重复导入。

## 安装方式

建议使用 Python 3.10+。

```bash
cd path/to/literature-agent-zotero-obsidian
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

## .env 配置方法

复制示例配置：

```bash
copy .env.example .env
```

按需填写：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=qwen-plus

ZOTERO_LIBRARY_ID=
ZOTERO_LIBRARY_TYPE=user
ZOTERO_API_KEY=

OBSIDIAN_VAULT_PATH=path/to/your/ObsidianVault
OBSIDIAN_LITERATURE_FOLDER=Literature Notes

APP_DATABASE_PATH=./literature_agent.db
```

没有 `OPENAI_API_KEY` 时，系统会使用启发式评分和摘要截断生成笔记总结。

## 获取 Zotero Library ID 和 API Key

1. 打开 https://www.zotero.org/settings/keys。
2. 创建一个新的 API Key，并勾选允许写入文库。
3. 个人文库的 `ZOTERO_LIBRARY_TYPE` 使用 `user`。
4. `ZOTERO_LIBRARY_ID` 是 Zotero 用户 ID，可在 Zotero API Keys 页面或 Zotero 个人资料相关页面找到。
5. 将 API Key 填入 `.env` 的 `ZOTERO_API_KEY`。

如果不配置 Zotero，应用仍可检索、评分，并在配置了 Obsidian 时生成 Markdown 笔记。

## 设置 Obsidian Vault 路径

将 `.env` 中的 `OBSIDIAN_VAULT_PATH` 设置为本地 Obsidian Vault 根目录，例如：

```env
OBSIDIAN_VAULT_PATH=path/to/your/ObsidianVault
OBSIDIAN_LITERATURE_FOLDER=Literature Notes
```

应用会自动在 Vault 下创建 `Literature Notes` 文件夹。文件名会自动移除 Windows 非法字符；如果同名笔记已存在，会追加 `-1`、`-2` 后缀。

## 运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

打开 Streamlit 给出的本地地址后即可使用。

## 当前 MVP 功能

- 输入研究主题或关键词。
- 使用 arXiv 检索候选论文；网络或 API 异常时回退到 mock 检索。
- 对候选论文进行相关性、创新性、方法价值评分。
- 无大模型 API 时使用启发式评分。
- 勾选论文后保存到 Zotero Collection。
- 为选中文献生成 Obsidian Markdown 文献笔记。
- 用 SQLite 记录已同步论文，优先按 DOI 去重，没有 DOI 时按标准化标题去重。
- Zotero 或 Obsidian 任一未配置时，另一侧仍可单独工作。

## 后续扩展方向

- Semantic Scholar 检索
- Crossref 检索
- PDF 下载与解析
- Zotero PDF 附件同步
- Obsidian Local REST API
- 向量数据库 RAG
- 每日自动文献推送

## 测试

```bash
pytest
```

当前测试覆盖：

- Obsidian 文件名清洗和 Markdown 写入。
- SQLite 初始化、DOI 去重、标题标准化去重。
- 同步服务对重复论文的跳过逻辑。
