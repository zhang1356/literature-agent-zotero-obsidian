import streamlit as st


CLAUDE_LIKE_CSS = """
<style>
:root {
  --la-background: #F7F1E8;
  --la-surface: #FBF7F0;
  --la-surface-alt: #F1E8DC;
  --la-border: #D8CFC2;
  --la-text-primary: #2D2A26;
  --la-text-secondary: #6B6258;
  --la-text-muted: #8A8178;
  --la-accent: #D97757;
  --la-accent-hover: #C86645;
  --la-accent-soft: #F3D8C8;
  --la-success: #6F8F72;
  --la-warning: #B88746;
  --la-danger: #B85C50;
}

.stApp {
  background: #F7F1E8;
  color: #2D2A26;
}

[data-testid="stSidebar"] {
  background: #F1E8DC;
  border-right: 1px solid #D8CFC2;
}

h1, h2, h3, h4, h5, h6, p, label, span {
  color: #2D2A26;
}

.stButton > button {
  background: #D97757;
  color: #FFFDF8;
  border: 1px solid #C86645;
  border-radius: 10px;
  box-shadow: none;
}

.stButton > button:hover {
  background: #C86645;
  color: #FFFDF8;
  border-color: #C86645;
}

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stTextArea textarea {
  background: #FBF7F0;
  border-color: #D8CFC2;
  border-radius: 10px;
  color: #2D2A26;
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
  background: #FBF7F0;
  border: 1px solid #D8CFC2;
  border-radius: 12px;
  overflow: hidden;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
}

.stTabs [data-baseweb="tab"] {
  background: #F1E8DC;
  border-radius: 999px;
  border: 1px solid #D8CFC2;
  color: #6B6258;
  padding: 8px 16px;
}

.stTabs [aria-selected="true"] {
  background: #F3D8C8;
  color: #2D2A26;
}

.la-hero {
  background: #FBF7F0;
  border: 1px solid #D8CFC2;
  border-radius: 18px;
  padding: 28px 30px;
  margin-bottom: 22px;
}

.la-hero-title {
  font-size: 2.2rem;
  font-weight: 720;
  line-height: 1.15;
  color: #2D2A26;
}

.la-hero-subtitle {
  font-size: 1.02rem;
  color: #6B6258;
  margin-top: 8px;
}

.la-card {
  background: #FBF7F0;
  border: 1px solid #D8CFC2;
  border-radius: 14px;
  padding: 18px;
  margin: 10px 0;
}

.la-card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #2D2A26;
  margin-bottom: 6px;
}

.la-muted,
.la-small {
  color: #8A8178;
}

.la-small {
  font-size: 0.86rem;
}

.la-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.82rem;
  border: 1px solid #D8CFC2;
  background: #F1E8DC;
  color: #6B6258;
  margin: 2px 4px 2px 0;
}

.la-badge-success {
  background: #E4EBDD;
  color: #4F6F52;
  border-color: #BFD0B4;
}

.la-badge-warning {
  background: #F4E4CB;
  color: #8A642C;
  border-color: #DDC394;
}

.la-badge-danger {
  background: #F1D7D2;
  color: #8B4138;
  border-color: #D8ABA4;
}

.la-badge-neutral {
  background: #F1E8DC;
  color: #6B6258;
}

.la-divider {
  border-top: 1px solid #D8CFC2;
  margin: 16px 0;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CLAUDE_LIKE_CSS, unsafe_allow_html=True)


def get_status_badge(label: str, configured: bool) -> str:
    css_class = "la-badge-success" if configured else "la-badge-neutral"
    status = "已配置" if configured else "未配置"
    return f'<span class="la-badge {css_class}">{label}：{status}</span>'


def get_recommendation_badge(score: float | None) -> str:
    score = score or 0
    if score > 80:
        return '<span class="la-badge la-badge-success">强烈推荐</span>'
    if score >= 60:
        return '<span class="la-badge la-badge-warning">可读</span>'
    return '<span class="la-badge la-badge-neutral">暂不推荐</span>'
