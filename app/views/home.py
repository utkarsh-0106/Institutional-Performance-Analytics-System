"""IPAS executive home / institutional intelligence command center."""
import html
from pathlib import Path
import base64

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.components import ui
from app.components.charts import ranking_distribution_chart
from app.ui_common import load_data, safe_plotly, show_data_banner, widget_key
from auth.session import get_current_user
from services.insights_service import InsightsService


def _safe(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _image_uri(filename: str) -> str:
    path = Path(__file__).resolve().parents[1] / "assets" / filename
    if not path.exists():
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _topbar(user, inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> None:
    """Interactive product header backed only by current session/data."""
    name = _safe(user.get("username", "User"))
    role = _safe(str(user.get("role", "user")).replace("_", " ").title())
    initials = _safe(name[:1].upper() if name else "U")
    choices = []
    if inst_df is not None and not inst_df.empty and "institution_name" in inst_df.columns:
        choices = sorted({str(v) for v in inst_df["institution_name"].dropna() if str(v).strip()})

    left, search_col, notif_col, profile_col = st.columns([1.15, 4.7, .65, 1.7], gap="small", vertical_alignment="center")
    with left:
        ui.html('<div class="ipa-topbar-context"><span>EXECUTIVE</span><small>Analytics workspace</small></div>')
    with search_col:
        query = st.text_input(
            "Global search",
            placeholder="Search institutions...",
            label_visibility="collapsed",
            key=widget_key("home", "global-search"),
        ).strip()
        if query:
            matches = [x for x in choices if query.lower() in x.lower()][:8]
            if matches:
                selected = st.selectbox(
                    "Matching institutions",
                    matches,
                    label_visibility="collapsed",
                    key=widget_key("home", "search-result"),
                )
                if st.button("Open institution profile", key=widget_key("home", "open-search"), type="primary"):
                    st.session_state["institution_profile_selection"] = selected
                    st.session_state["sidebar_nav_page"] = "Institution Profile"
                    st.rerun()
            else:
                st.caption("No institutions match the current search.")
    with notif_col:
        with st.popover("●", use_container_width=True):
            st.markdown("**System status**")
            missing = [c for c in ["institution_name", "student_enrollment", "faculty_count", "placement_percentage"] if c not in inst_df.columns]
            if missing:
                st.warning("Required dataset fields missing: " + ", ".join(missing))
            elif inst_df.empty:
                st.warning("The current dataset contains no institution records.")
            else:
                st.success(f"Dataset loaded · {len(inst_df):,} institution records")
                st.caption("Status is derived from the current analytics dataset; no notifications are fabricated.")
    with profile_col:
        with st.popover(f"{initials}  {name}", use_container_width=True):
            st.markdown(f"**{name}**")
            st.caption(role)
            linked = user.get("linked_institution")
            if linked:
                st.caption(f"Institution · {linked}")
            if st.button("View institution profile", key=widget_key("home", "profile-menu"), use_container_width=True):
                if linked:
                    st.session_state["institution_profile_selection"] = linked
                st.session_state["sidebar_nav_page"] = "Institution Profile"
                st.rerun()
            if st.button("Sign out", key=widget_key("home", "sign-out"), use_container_width=True):
                from auth.session import logout_user
                logout_user()
                st.rerun()


def _hero(user, total: int) -> None:
    uri = _image_uri("campus-hero.jpg")
    name = _safe(user.get("username", "User"))
    role = _safe(str(user.get("role", "user")).replace("_", " ").title())
    image_markup = f'<img src="{uri}" alt="Institutional campus" />' if uri else ""
    ui.html(f"""
    <section class="ipa-exec-hero ipa-exec-hero-v5">
      <div class="ipa-exec-hero-media">{image_markup}</div>
      <div class="ipa-exec-hero-overlay"></div>
      <div class="ipa-exec-hero-copy">
        <div class="ipa-exec-eyebrow"><span>IPAS</span> · INSTITUTIONAL INTELLIGENCE</div>
        <h1>Welcome back, {name}!</h1>
        <p>Measure institutional performance, compare outcomes, and turn current evidence into confident decisions.</p>
        <div class="ipa-exec-hero-meta">
          <span><b>{total:,}</b> institutions</span>
          <span><b>4</b> integrated sources</span>
          <span>{role} workspace</span>
        </div>
      </div>
      <div class="ipa-exec-quote">
        <div class="ipa-quote-mark">“</div>
        <p>Data-driven insights for stronger, smarter institutions.</p>
        <div class="ipa-quote-rule"></div>
        <span>Measure · Compare · Explain · Improve</span>
      </div>
    </section>
    """)


def _quick_actions() -> None:
    ui.html('<div class="ipa-exec-section-head ipa-section-tight"><div><span>QUICK ACTIONS</span><small>Move directly into a decision workflow</small></div></div>')
    cols = st.columns(4, gap="medium")
    actions = [
        ("⇧", "Upload Data", "Validate and process institutional sources", "Data Management", "blue"),
        ("▥", "View Rankings", "Explore weighted performance rankings", "Rankings", "green"),
        ("⌁", "ML Predictions", "Review model-based outputs", "ML Predictions", "amber"),
        ("▤", "Generate Report", "Create an evidence-based report", "Reports", "red"),
    ]
    for col, (icon, title, desc, page, tone) in zip(cols, actions):
        with col:
            st.markdown(f'<div class="ipa-action-shell {tone}"><span class="ipa-action-icon">{icon}</span><div><strong>{_safe(title)}</strong><small>{_safe(desc)}</small></div></div>', unsafe_allow_html=True)
            if st.button("Open workspace", key=widget_key("home-action", page), use_container_width=True):
                st.session_state["sidebar_nav_page"] = page
                st.rerun()


def _headline_stats(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> None:
    total = len(inst_df)
    avg_students = inst_df["student_enrollment"].mean() if not inst_df.empty and "student_enrollment" in inst_df else 0
    avg_placement = inst_df["placement_percentage"].mean() if not inst_df.empty and "placement_percentage" in inst_df else 0
    publications = inst_df["research_publications"].sum() if not inst_df.empty and "research_publications" in inst_df else 0
    ui.stat_grid([
        {"label": "Total Institutions", "value": f"{total:,}", "hint": "Current analytics universe", "icon_name": "building", "tone": "primary"},
        {"label": "Avg. Student Enrollment", "value": f"{avg_students:,.0f}", "hint": "Across all institutions", "icon_name": "users", "tone": "accent"},
        {"label": "Avg. Placement", "value": f"{avg_placement:.1f}", "unit": "%", "hint": "Current institutional average", "icon_name": "briefcase", "tone": "success"},
        {"label": "Research Publications", "value": f"{publications:,.0f}", "hint": "Total publications tracked", "icon_name": "flask", "tone": "warning"},
    ])


def _performance_chart(kpi_df: pd.DataFrame) -> None:
    mapping = [("Academic", "academic_score"), ("Research", "research_score"), ("Placement", "placement_score"), ("Infrastructure", "infrastructure_score_kpi"), ("Faculty", "faculty_score"), ("Accreditation", "accreditation_score")]
    rows = [{"KPI": label, "Score": float(kpi_df[col].mean())} for label, col in mapping if col in kpi_df.columns]
    if not rows:
        ui.empty_state("No KPI data", "KPI data is required for this view.", icon_name="chart-bar")
        return
    frame = pd.DataFrame(rows).sort_values("Score")
    fig = px.bar(frame, x="Score", y="KPI", orientation="h", text="Score")
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", marker_color="#2469ad", hovertemplate="%{y}: %{x:.1f}<extra></extra>")
    fig.update_layout(height=360, margin=dict(l=12, r=44, t=10, b=10), paper_bgcolor="white", plot_bgcolor="white", font=dict(color="#15263d"), showlegend=False, bargap=.34)
    fig.update_xaxes(range=[0, 105], gridcolor="#e8edf3", zeroline=False, title=None, tickfont=dict(size=10, color="#8795a6"))
    fig.update_yaxes(title=None, showgrid=False, tickfont=dict(size=11, color="#43566e"))
    ui.chart(fig, key=widget_key("home", "kpi-landscape"))


def _kpi_radar(kpi_df: pd.DataFrame) -> None:
    mapping = [("Academic", "academic_score"), ("Research", "research_score"), ("Placement", "placement_score"), ("Infrastructure", "infrastructure_score_kpi"), ("Faculty", "faculty_score"), ("Accreditation", "accreditation_score")]
    labels, values = [], []
    for label, col in mapping:
        if col in kpi_df.columns:
            labels.append(label)
            values.append(float(kpi_df[col].mean()))
    if not values:
        ui.empty_state("No KPI data", "KPI data is required for this view.", icon_name="chart-bar")
        return
    labels += [labels[0]]
    values += [values[0]]
    fig = go.Figure(go.Scatterpolar(r=values, theta=labels, fill="toself", line=dict(color="#2f6fad", width=2), fillcolor="rgba(47,111,173,.16)", hovertemplate="%{theta}: %{r:.1f}<extra></extra>"))
    fig.update_layout(height=350, margin=dict(l=32,r=32,t=14,b=14), paper_bgcolor="white", polar=dict(radialaxis=dict(range=[0,100], showticklabels=True, gridcolor="#e6edf5"), angularaxis=dict(gridcolor="#e6edf5")), showlegend=False)
    ui.chart(fig, key=widget_key("home", "kpi-radar"))


def _top_institutions(kpi_df: pd.DataFrame) -> None:
    if kpi_df.empty:
        ui.empty_state("No ranking data", "Ranking records will appear after KPI processing.", icon_name="award")
        return
    cols = [c for c in ["institution_name", "institution_rank", "composite_rank_score", "ranking_category"] if c in kpi_df.columns]
    frame = kpi_df[cols].sort_values("institution_rank").head(5)
    for idx, (_, row) in enumerate(frame.iterrows(), start=1):
        name = str(row.get("institution_name", ""))
        rank = int(row.get("institution_rank", 0))
        score = float(row.get("composite_rank_score", 0))
        category = str(row.get("ranking_category", ""))
        c1, c2, c3, c4 = st.columns([.45, 3.4, 1.1, 1.45], gap="small", vertical_alignment="center")
        with c1:
            st.markdown(f"**{rank}**")
        with c2:
            st.markdown(f"**{_safe(name)}**", unsafe_allow_html=True)
            st.caption(category)
        with c3:
            st.markdown(f"**{score:.1f}**")
        with c4:
            if st.button("View profile", key=widget_key("home-top", idx), use_container_width=True):
                st.session_state["institution_profile_selection"] = name
                st.session_state["sidebar_nav_page"] = "Institution Profile"
                st.rerun()
        if idx < len(frame):
            st.divider()


def render():
    user = get_current_user()
    data = load_data()
    inst_df, kpi_df = data["institutions"], data["kpis"]
    total = len(inst_df)

    _topbar(user, inst_df, kpi_df)
    _hero(user, total)
    show_data_banner(data)
    _quick_actions()

    ui.html('<div class="ipa-exec-section-head"><div><span>PERFORMANCE SNAPSHOT</span><small>Live values from the current dataset</small></div></div>')
    _headline_stats(inst_df, kpi_df)
    ui.html('<div class="ipa-data-strip"><span class="ipa-data-strip-dot"></span><strong>Data integrity</strong><span>Current dataset loaded successfully</span><span class="ipa-data-strip-sep">•</span><span>UGC · NIRF · AISHE · NAAC</span><span class="ipa-data-strip-spacer"></span><span>Live analytics</span></div>')

    ui.html('<div class="ipa-exec-section-head"><div><span>ANALYTICS AT A GLANCE</span><small>Current evidence — no fabricated historical trends</small></div></div>')
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        with ui.card(title="Performance Landscape", subtitle="Average score across the six existing KPI dimensions.", icon_name="chart-bar"):
            _performance_chart(kpi_df)
    with right:
        with ui.card(title="Top Performing Institutions", subtitle="Current weighted ranking results.", icon_name="award"):
            _top_institutions(kpi_df)

    a, b, c = st.columns([1, 1, 1], gap="large")
    with a:
        with ui.card(title="KPI Profile", subtitle="Average institutional KPI shape.", icon_name="radar"):
            _kpi_radar(kpi_df)
    with b:
        with ui.card(title="Ranking Distribution", subtitle="Current institution categories.", icon_name="pie-chart"):
            safe_plotly(ranking_distribution_chart, kpi_df, page="home", chart_name="rank_distribution")
    with c:
        insights = InsightsService.generate_system_insights(inst_df, kpi_df)
        with ui.card(title="Recent Insights", subtitle="Generated by the existing analytics service.", icon_name="sparkles"):
            if insights:
                for insight in insights[:4]:
                    ui.html(ui.insight_card(insight, label="System insight", tone="primary"))
            else:
                ui.empty_state("No insights available", "Insights require current institution and KPI records.", icon_name="sparkles")

    st.caption("IPAS · Institutional Performance Analytics · Current dataset")
