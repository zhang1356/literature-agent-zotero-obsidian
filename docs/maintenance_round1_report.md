# 第一轮维护报告

## 1. 本轮目标

本轮主要完成稳定性、透明化、科研可用性增强，重点避免真实科研流程中的静默造假：mock 数据、启发式评分、外部服务失败和本地路径错误都需要在 UI 或日志中明确暴露。

## 2. 修改文件清单

- `config.py`
- `models.py`
- `agents/search_agent.py`
- `agents/rank_agent.py`
- `agents/note_agent.py`
- `connectors/zotero_connector.py`
- `services/connection_tests.py`
- `services/sync_service.py`
- `database.py`
- `app.py`
- `config/user_config.example.json`
- `tests/test_round1_stability.py`
- `docs/maintenance_round1_report.md`

## 3. 主要修改内容

- 默认检索年份 2026：新增 `DEFAULT_START_YEAR = 2026` 和 `default_start_year` 配置项，Streamlit 检索页新增“起始年份”输入控件，并显示“当前检索范围：2026 年至今”。检索逻辑使用该起始年份进行 arXiv 后置过滤和 mock 结果过滤。
- mock 数据透明化：新增 `data_source` 字段，arXiv 结果标记为 `arxiv`，mock 回退结果标记为 `mock`，UI 显示 mock 警告和数据来源，日志记录 arXiv 失败或无结果后的 mock 回退原因。
- 启发式评分透明化：新增 `analysis_source` 字段，LLM 成功标记为 `llm`，无 API Key 或模型调用失败时标记为 `heuristic`，UI 显示启发式评分警告和评分来源，日志记录无 Key 和模型失败原因。
- Obsidian 模板升级：升级 Markdown 阅读卡片结构，包含基本信息、一句话总结、研究问题、方法结构、主要贡献、实验设置、局限性、可改进方向、可用于我项目的点、阅读状态和标签；缺失字段使用“待补充”；模板显示 `data_source` 和 `analysis_source`。
- Zotero 标签增强：写入 Zotero 时自动生成 `paper`、`ai-analyzed`、`read-later`、优先级标签、`mock-data` 和 `heuristic-score`。已有 Collection 支持已增强为默认使用 `AI Literature Agent/2026+` 子 Collection。
- 异常提示增强：无 API Key、arXiv 回退、Zotero 缺失、Obsidian 路径缺失或不可用、Zotero/Obsidian 写入失败、mock 数据和启发式评分均保留 UI 提示或日志记录。

## 4. 测试结果

执行命令：

```bash
python -m pytest
```

测试结果：31 passed，0 failed，2 warnings。

警告为依赖库 `google.protobuf` 在 Python 3.14 前的弃用提示，不是本轮代码失败。

## 5. 未完成或暂缓内容

- 未引入向量数据库。
- 未做 PDF 全文解析。
- 未做 Zotero PDF 注释提取。
- 未做复杂多智能体重构。
- 未生成新的发布 zip 包。
- 当前目录不是 git repository，因此本轮未执行 git 提交。

## 6. 风险与后续建议

- 建议下一轮增加 PDF 全文解析，但需要明确本地 PDF 存储和隐私边界。
- 建议增加 Zotero PDF 注释提取，用于自动生成阅读摘录。
- 建议引入轻量向量数据库前先完成可回滚的数据迁移设计。
- 建议增加多轮文献综述生成，但不要改变现有检索、评分、保存主流程。
- 建议补充 GitHub Actions 自动测试或本地等效 CI 脚本。
