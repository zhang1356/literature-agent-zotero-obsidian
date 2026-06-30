import streamlit as st


def render_hero() -> None:
    st.markdown(
        """
        <section class="la-hero">
          <div class="la-hero-title">文献检索智能体</div>
          <div class="la-hero-subtitle">连接 Zotero 与 Obsidian 的本地研究助理</div>
          <p class="la-muted">
            检索、评分、保存与沉淀文献，全流程默认保存在你的本地环境中。
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="la-card">
          <div class="la-card-title">{title}</div>
          <div class="la-muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_cards(total: int, zotero_count: int, obsidian_count: int) -> None:
    cols = st.columns(3)
    values = [
        ("总保存数", total),
        ("Zotero 已同步数", zotero_count),
        ("Obsidian 笔记数", obsidian_count),
    ]
    for col, (label, value) in zip(cols, values):
        with col:
            st.markdown(
                f"""
                <div class="la-card">
                  <div class="la-small">{label}</div>
                  <div class="la-hero-title" style="font-size: 1.8rem;">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
