import pandas as pd
import streamlit as st
from pathlib import Path

import config
import database
from agents.rank_agent import RankAgent
from agents.search_agent import SearchAgent
from connectors.obsidian_connector import ObsidianConnector
from connectors.zotero_connector import ZoteroConnector
from logger import get_logger
from models import Paper
from services.connection_tests import (
    test_model_api,
    test_obsidian_path,
    test_zotero_connection,
)
from services.local_status import check_local_environment
from services.sync_service import SyncService
from ui.components import render_hero, render_stat_cards
from ui.theme import apply_theme, get_recommendation_badge, get_status_badge


logger = get_logger(__name__)

st.set_page_config(page_title="文献检索智能体", layout="wide")
apply_theme()


def current_settings():
    config.get_settings.cache_clear()
    return config.get_settings()


settings = current_settings()


def sqlite_status() -> tuple[bool, str]:
    try:
        database.init_db()
        return True, "已连接"
    except Exception as exc:
        logger.exception("数据库异常")
        return False, "未连接"


def build_connectors(active_settings):
    zotero = None
    obsidian = None
    errors: list[str] = []

    if active_settings.has_zotero:
        try:
            zotero = ZoteroConnector(
                active_settings.zotero_library_id,
                active_settings.zotero_library_type,
                active_settings.zotero_api_key,
            )
        except Exception as exc:
            message = "Zotero 初始化失败：请检查 Library ID、Library Type 和 API Key。"
            logger.exception("Zotero 初始化失败：%s", exc)
            errors.append(message)

    if active_settings.has_obsidian:
        try:
            obsidian = ObsidianConnector(
                active_settings.obsidian_vault_path,
                active_settings.obsidian_literature_folder,
            )
        except Exception as exc:
            message = "Obsidian 初始化失败：请检查 Vault 路径是否正确。"
            logger.exception("Obsidian 初始化失败：%s", exc)
            errors.append(message)

    return zotero, obsidian, errors


def recommendation_level(score: float | None) -> str:
    score = score or 0
    if score > 80:
        return "强烈推荐"
    if score >= 60:
        return "可读"
    return "暂不推荐"


def data_source_label(value: str) -> str:
    labels = {
        "arxiv": "arXiv",
        "mock": "mock 示例数据",
        "local": "本地数据",
        "unknown": "未知",
    }
    return labels.get(value or "unknown", value)


def analysis_source_label(value: str) -> str:
    labels = {
        "llm": "LLM",
        "heuristic": "启发式规则",
        "mock": "mock 示例",
        "none": "未评分",
    }
    return labels.get(value or "none", value)


def abstract_preview(abstract: str | None, length: int = 120) -> str:
    if not abstract:
        return ""
    abstract = " ".join(abstract.split())
    return abstract if len(abstract) <= length else abstract[:length] + "..."


def papers_to_dataframe(papers: list[Paper]) -> tuple[pd.DataFrame, list[Paper]]:
    sorted_papers = sorted(papers, key=lambda item: item.relevance_score or 0, reverse=True)
    rows = []
    for idx, paper in enumerate(sorted_papers):
        rows.append(
            {
                "选择": False,
                "序号": idx,
                "推荐等级": recommendation_level(paper.relevance_score),
                "标题": paper.title,
                "年份": paper.year,
                "作者": ", ".join(paper.authors[:3]),
                "来源": paper.source,
                "数据来源": data_source_label(paper.data_source),
                "相关性评分": paper.relevance_score,
                "评分来源": analysis_source_label(paper.analysis_source),
                "标签": ", ".join(paper.tags),
                "摘要预览": abstract_preview(paper.abstract),
                "推荐理由": paper.reason,
                "DOI/URL": paper.doi or paper.url or "",
            }
        )
    return pd.DataFrame(rows), sorted_papers


def saved_papers_dataframe(saved_papers=None, show_obsidian_path: bool = True) -> pd.DataFrame:
    saved_papers = saved_papers if saved_papers is not None else database.list_saved_papers()
    rows = [
        {
            "标题": paper.title,
            "年份": paper.year,
            "DOI": paper.doi,
            "标签": ", ".join(paper.tags),
            "Zotero Key": paper.zotero_key,
            "Obsidian 路径": paper.obsidian_path,
            "保存时间": paper.created_at,
        }
        for paper in saved_papers
    ]
    if not show_obsidian_path:
        for row in rows:
            row.pop("Obsidian 路径", None)
    return pd.DataFrame(
        rows
    )


def zotero_item_title(item: dict) -> str:
    return item.get("data", {}).get("title") or item.get("title") or "(无标题)"


def status_icon(ok: bool) -> str:
    return "✅" if ok else "⚠️"


def render_sidebar(active_settings, sqlite_message: str, local_status: dict) -> None:
    st.sidebar.markdown("### 配置状态")
    st.sidebar.markdown(
        " ".join(
            [
                get_status_badge("模型 API", active_settings.has_openai),
                get_status_badge("Zotero", active_settings.has_zotero),
                get_status_badge("Obsidian", active_settings.has_obsidian),
                get_status_badge("SQLite", sqlite_message == "已连接"),
            ]
        ),
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="la-divider"></div>', unsafe_allow_html=True)
    st.sidebar.caption("API Key 仅显示配置状态，不会在页面明文展示。")
    st.sidebar.markdown("### 本地状态检查")
    checks = local_status["checks"]
    status_rows = [
        ("本地配置", checks["config_user"]["ok"], checks["config_user"]["message"]),
        ("Obsidian Vault", checks["obsidian"]["ok"], checks["obsidian"]["message"]),
        ("Zotero", checks["zotero"]["ok"], checks["zotero"]["message"]),
        ("模型 API", checks["model_api"]["ok"], checks["model_api"]["message"]),
        ("数据库", sqlite_message == "已连接", "可用" if sqlite_message == "已连接" else "不可用"),
        ("日志目录", checks["logs_dir"]["ok"], checks["logs_dir"]["message"]),
        ("当前检索起始年份", True, checks["default_start_year"]["message"]),
    ]
    for label, ok, message in status_rows:
        st.sidebar.caption(f"{status_icon(ok)} {label}：{message}")


def should_show_first_use_guide(active_settings) -> bool:
    no_user_config = not config.USER_CONFIG_PATH.exists()
    no_integrations = not (
        active_settings.has_obsidian
        or active_settings.has_zotero
        or active_settings.has_openai
    )
    return no_user_config or no_integrations


def render_first_use_guide(active_settings) -> None:
    if not should_show_first_use_guide(active_settings):
        return
    st.markdown(
        """
        <div class="la-card">
          <div class="la-card-title">欢迎使用文献检索智能体。</div>
          <div class="la-muted">
            建议先进入“系统设置”，至少配置 Obsidian Vault Path，这样可以把筛选后的论文保存为本地 Markdown 笔记。
            如果暂时没有 Zotero 或模型 API，也可以先使用基础检索和启发式评分。
          </div>
          <ul class="la-muted">
            <li>去系统设置：打开上方“系统设置”页，填写并保存路径或 API 配置。</li>
            <li>没有模型 API 也可以使用：系统会自动使用启发式评分。</li>
            <li>只用 Obsidian 不用 Zotero 也可以：保存时将仅生成 Markdown 笔记。</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_local_status_panel(local_status: dict) -> None:
    warnings = local_status.get("warnings", [])
    if not warnings:
        return
    st.markdown(
        '<div class="la-card-title">本地状态检查</div>',
        unsafe_allow_html=True,
    )
    for warning in warnings:
        st.warning(warning)


def render_search_tab(active_settings) -> None:
    st.markdown('<div class="la-card-title">文献检索</div>', unsafe_allow_html=True)
    if "pending_search_query" in st.session_state:
        st.session_state.search_query = st.session_state.pop("pending_search_query")
    query = st.text_input(
        "研究主题 / 关键词",
        placeholder="例如：multimodal RAG for scientific literature",
        key="search_query",
    )
    examples = [
        "audio visual question answering",
        "retrieval augmented generation survey",
        "multimodal large language model",
        "academic literature recommendation",
        "graph neural network review",
    ]
    example_cols = st.columns(len(examples))
    for col, example in zip(example_cols, examples):
        with col:
            if st.button(example, key=f"example_{example}"):
                st.session_state.pending_search_query = example
                st.rerun()

    st.caption(
        "年份起始用于过滤更早论文；最大检索数量控制候选论文数量；如果 arXiv 检索失败，会自动回退到 mock 检索。"
    )
    default_start_year = int(active_settings.default_start_year or config.DEFAULT_START_YEAR)
    col_year, col_count, col_collection = st.columns([1, 1, 2])
    with col_year:
        year_from = st.number_input(
            "起始年份",
            value=default_start_year,
            min_value=1900,
            max_value=2100,
        )
    with col_count:
        max_results = st.number_input(
            "最大检索数量", value=10, min_value=1, max_value=50
        )
    with col_collection:
        collection_name = st.text_input(
            "Zotero Collection 名称", value="AI Literature Agent"
        )
    st.caption(f"当前检索范围：{int(year_from)} 年至今")
    if not active_settings.has_openai:
        st.warning("未配置模型 API Key。检索后将使用启发式评分，结果仅供参考。")

    if "ranked_papers" not in st.session_state:
        st.session_state.ranked_papers = []

    if st.button("检索并评分", type="primary"):
        if not query.strip():
            st.warning("请输入研究主题或关键词。")
        else:
            with st.spinner("正在检索并评分..."):
                try:
                    service = SyncService(auto_connect=False)
                    st.session_state.ranked_papers = service.search_and_rank(
                        query.strip(), int(year_from), int(max_results)
                    )
                    st.success(
                        f"完成检索与评分，共 {len(st.session_state.ranked_papers)} 篇候选论文。"
                    )
                except Exception as exc:
                    logger.exception("检索或评分失败")
                    st.error("网络异常：外部检索失败，已回退到 mock 检索；如仍失败，请查看日志。")

    ranked_papers: list[Paper] = st.session_state.ranked_papers
    if not ranked_papers:
        st.info("输入关键词后开始检索。未配置模型 API 时会使用启发式评分。")
        return

    source_notice = SearchAgent.source_notice(ranked_papers)
    analysis_notice = RankAgent.analysis_notice(ranked_papers)
    if source_notice:
        st.warning(source_notice)
    if analysis_notice:
        st.warning(analysis_notice)

    st.markdown(
        " ".join(get_recommendation_badge(paper.relevance_score) for paper in ranked_papers[:3]),
        unsafe_allow_html=True,
    )
    display_df, sorted_papers = papers_to_dataframe(ranked_papers)
    edited_df = st.data_editor(
        display_df,
        hide_index=True,
        disabled=[
            "序号",
            "推荐等级",
            "标题",
            "年份",
            "作者",
            "来源",
            "数据来源",
            "相关性评分",
            "评分来源",
            "标签",
            "摘要预览",
            "推荐理由",
            "DOI/URL",
        ],
        column_config={"选择": st.column_config.CheckboxColumn("选择")},
        use_container_width=True,
        key="paper_selection_editor",
    )

    st.markdown("#### 候选文献详情")
    for idx, paper in enumerate(sorted_papers):
        with st.expander(f"{idx + 1}. {paper.title}"):
            st.caption(
                f"来源：{data_source_label(paper.data_source)}；"
                f"评分来源：{analysis_source_label(paper.analysis_source)}"
            )
            st.write(paper.abstract or "待补充")

    selected_indices = edited_df.loc[edited_df["选择"], "序号"].tolist()
    selected_papers = [sorted_papers[int(index)] for index in selected_indices]

    can_save = active_settings.has_zotero or active_settings.has_obsidian
    if not can_save:
        st.info("Zotero 和 Obsidian 都未配置。当前仅支持检索和评分，无法保存。")
    elif active_settings.has_obsidian and not active_settings.has_zotero:
        st.info("将仅保存 Obsidian 笔记。尚未配置 Zotero，已跳过 Zotero 同步。")
    elif active_settings.has_zotero and not active_settings.has_obsidian:
        st.info("将仅写入 Zotero。尚未配置 Obsidian，无法生成 Markdown 笔记。")
    else:
        st.info("已配置 Zotero 和 Obsidian，保存时会同步两边。")

    if active_settings.has_obsidian:
        literature_path = (
            f"{active_settings.obsidian_vault_path}/{active_settings.obsidian_literature_folder}"
        )
        st.caption(f"Obsidian 文献笔记路径：{literature_path}")

    if st.button("保存选中文献", disabled=not can_save):
        if not selected_papers:
            st.warning("请先勾选至少一篇论文。")
            return

        zotero, obsidian, connector_errors = build_connectors(active_settings)
        for error in connector_errors:
            st.error(error)

        if not zotero and not obsidian:
            st.error("没有可用的 Zotero 或 Obsidian 连接，保存已取消。")
            return

        with st.spinner("正在保存选中文献..."):
            service = SyncService(
                zotero_connector=zotero,
                obsidian_connector=obsidian,
                auto_connect=False,
            )
            results = service.save_selected_papers(
                selected_papers, collection_name, year_from=int(year_from)
            )
        st.subheader("保存结果")
        display_columns = [
            "标题",
            "Zotero",
            "Obsidian",
            "SQLite",
            "Obsidian 文件路径",
            "Zotero Key",
            "错误原因",
        ]
        st.dataframe(pd.DataFrame(results)[display_columns], use_container_width=True)


def render_saved_tab(active_settings) -> None:
    st.markdown('<div class="la-card-title">已保存文献</div>', unsafe_allow_html=True)
    try:
        saved_papers = database.list_saved_papers()
        total = len(saved_papers)
        zotero_count = sum(1 for paper in saved_papers if paper.zotero_key)
        obsidian_count = sum(1 for paper in saved_papers if paper.obsidian_path)
        render_stat_cards(total, zotero_count, obsidian_count)

        if not saved_papers:
            st.info("还没有保存文献。请先在“文献检索”页检索并保存论文。")
        else:
            search_query = st.text_input(
                "搜索已保存文献", placeholder="可按标题、DOI、标签搜索"
            )
            years = sorted({paper.year for paper in saved_papers if paper.year}, reverse=True)
            year_options = ["全部年份"] + [str(year) for year in years]
            selected_year = st.selectbox("按年份筛选", year_options)
            year_value = None if selected_year == "全部年份" else int(selected_year)
            filtered = database.search_saved_papers(search_query, year_value, saved_papers)
            obsidian_root_exists = (
                active_settings.has_obsidian
                and Path(active_settings.obsidian_vault_path).expanduser().exists()
            )
            saved_df = saved_papers_dataframe(
                filtered, show_obsidian_path=obsidian_root_exists
            )
            st.download_button(
                "导出 CSV",
                data=database.saved_papers_to_csv(filtered).encode("utf-8-sig"),
                file_name="saved_literature.csv",
                mime="text/csv",
                disabled=not filtered,
            )
            st.dataframe(saved_df, use_container_width=True)
    except Exception as exc:
        logger.exception("读取已保存文献失败")
        st.error("读取已保存文献失败，请查看日志。")


def render_settings_tab(active_settings) -> None:
    st.markdown('<div class="la-card-title">系统设置</div>', unsafe_allow_html=True)
    st.markdown(
        " ".join(
            [
                get_status_badge("模型 API", active_settings.has_openai),
                get_status_badge("Zotero", active_settings.has_zotero),
                get_status_badge("Obsidian", active_settings.has_obsidian),
            ]
        ),
        unsafe_allow_html=True,
    )

    current = config.settings_as_dict(active_settings)
    with st.form("user_config_form"):
        st.subheader("模型 API")
        openai_api_key = st.text_input(
            "OpenAI / Qwen / DeepSeek API Key",
            value="",
            type="password",
            placeholder="留空则保留已有 Key",
        )
        openai_base_url = st.text_input(
            "OpenAI Base URL", value=current["openai_base_url"]
        )
        openai_model = st.text_input("模型名称", value=current["openai_model"])

        st.subheader("Zotero")
        zotero_library_id = st.text_input(
            "Zotero Library ID", value=current["zotero_library_id"]
        )
        zotero_library_type = st.selectbox(
            "Zotero Library Type",
            options=["user", "group"],
            index=0 if current["zotero_library_type"] != "group" else 1,
        )
        zotero_api_key = st.text_input(
            "Zotero API Key",
            value="",
            type="password",
            placeholder="留空则保留已有 Key",
        )

        st.subheader("Obsidian")
        obsidian_vault_path = st.text_input(
            "Obsidian Vault Path", value=current["obsidian_vault_path"]
        )
        obsidian_literature_folder = st.text_input(
            "Obsidian Literature Folder",
            value=current["obsidian_literature_folder"],
        )
        app_database_path = st.text_input(
            "SQLite 数据库路径", value=current["app_database_path"]
        )

        submitted = st.form_submit_button("保存配置", type="primary")

    if submitted:
        payload = {
            "openai_api_key": current["openai_api_key"],
            "openai_base_url": openai_base_url,
            "openai_model": openai_model,
            "zotero_library_id": zotero_library_id,
            "zotero_library_type": zotero_library_type,
            "zotero_api_key": current["zotero_api_key"],
            "obsidian_vault_path": obsidian_vault_path,
            "obsidian_literature_folder": obsidian_literature_folder,
            "app_database_path": app_database_path,
        }
        if openai_api_key:
            payload["openai_api_key"] = openai_api_key
        if zotero_api_key:
            payload["zotero_api_key"] = zotero_api_key
        saved_path = config.save_user_config(payload)
        st.success(f"配置已保存到 {saved_path}。请重启应用后生效。")

    st.markdown('<div class="la-divider"></div>', unsafe_allow_html=True)
    st.subheader("连接测试")
    st.caption("请先保存配置，再使用下面的测试按钮。API Key 不会在页面明文显示。")
    test_cols = st.columns(3)
    with test_cols[0]:
        if st.button("测试 Obsidian 路径"):
            ok, message = test_obsidian_path(
                active_settings.obsidian_vault_path,
                active_settings.obsidian_literature_folder,
            )
            st.success(message) if ok else st.error(message)
    with test_cols[1]:
        if st.button("测试 Zotero 连接"):
            ok, message = test_zotero_connection(active_settings)
            st.success(message) if ok else st.error(message)
    with test_cols[2]:
        if st.button("测试模型 API"):
            ok, message = test_model_api(active_settings)
            st.success(message) if ok else st.error(message)

    st.markdown('<div class="la-divider"></div>', unsafe_allow_html=True)
    st.subheader("查看 Zotero 最近文献")
    if not active_settings.has_zotero:
        st.info("Zotero 未配置。")
    elif st.button("读取最近 10 条 Zotero 文献"):
        zotero, _, errors = build_connectors(active_settings)
        for error in errors:
            st.error(error)
        if zotero:
            try:
                recent_items = zotero.get_recent_items(limit=10)
                st.dataframe(
                    pd.DataFrame(
                        [{"标题": zotero_item_title(item)} for item in recent_items]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            except Exception as exc:
                logger.exception("读取 Zotero 最近文献失败：%s", exc)
                st.error("读取 Zotero 最近文献失败，请检查 API Key 和网络连接。")

    st.subheader("搜索 Obsidian 文献笔记")
    if not active_settings.has_obsidian:
        st.info("Obsidian 未配置。")
    else:
        keyword = st.text_input("Obsidian 笔记关键词", key="obsidian_note_keyword")
        if keyword.strip():
            try:
                connector = ObsidianConnector(
                    active_settings.obsidian_vault_path,
                    active_settings.obsidian_literature_folder,
                )
                note_results = connector.search_notes(keyword)
                if note_results:
                    st.dataframe(pd.DataFrame(note_results), use_container_width=True)
                else:
                    st.info("没有匹配的 Obsidian 文献笔记。")
            except Exception as exc:
                logger.exception("搜索 Obsidian 文献笔记失败：%s", exc)
                st.error("搜索 Obsidian 文献笔记失败，请检查 Vault 路径是否正确。")


sqlite_ok, sqlite_message = sqlite_status()
local_status = check_local_environment(settings)
render_hero()
render_first_use_guide(settings)
render_local_status_panel(local_status)
render_sidebar(settings, sqlite_message, local_status)

tab_search, tab_saved, tab_settings = st.tabs(["文献检索", "已保存文献", "系统设置"])

with tab_search:
    render_search_tab(settings)

with tab_saved:
    render_saved_tab(settings)

with tab_settings:
    render_settings_tab(settings)
