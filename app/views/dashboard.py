"""Institutional analytics dashboard — presentation layer only."""
import html

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components import ui
from app.components.charts import (
    kpi_comparison_chart,
    placement_analysis_chart,
    research_analysis_chart,
    ranking_distribution_chart,
)
from app.ui_common import (
    load_data,
    safe_plotly,
    show_data_banner,
    widget_key,
)
from auth.session import get_current_user
from services.insights_service import InsightsService


def _safe_text(value) -> str:
    return html.escape("" if value is None else str(value))


def _fmt_int(value) -> str:
    return f"{int(value):,}"


def _ranking_category_tone(category: str) -> str:
    value = str(category or "").lower()
    if "50" in value:
        return "success"
    if "200" in value:
        return "primary"
    return "warning"


def _render_dashboard_header(user: dict) -> None:
    name = str(user.get("username") or "User").replace("_", " ").title()
    role = str(user.get("role") or "User").replace("_", " ").title()
    ui.html(
        f"""
        <div class="ipa-dashboard-topbar">
          <div>
            <div class="ipa-kicker">Institutional Intelligence</div>
            <h1>Performance Command Center</h1>
            <p>Monitor institutional health, compare performance, and move from evidence to action.</p>
          </div>
          <div class="ipa-user-chip">
            <div class="ipa-user-avatar">{_safe_text(name[:1].upper())}</div>
            <div>
              <strong>{_safe_text(name)}</strong>
              <span>{_safe_text(role)}</span>
            </div>
          </div>
        </div>
        """
    )


def _render_hero(user: dict, data: dict) -> None:
    name = str(user.get("username") or "User").replace("_", " ").title()
    total = len(data["institutions"])
    image_uri = ui.image_data_uri("campus-quad.jpg")
    background = (
        f"linear-gradient(90deg, rgba(7,20,40,.94) 0%, rgba(11,31,58,.80) 48%, rgba(11,31,58,.30) 100%), url('{image_uri}')"
        if image_uri
        else "linear-gradient(135deg, #0b1f3a, #1e4e8c)"
    )
    ui.html(
        f"""
        <div class="ipa-dashboard-hero" style="background-image:{background}">
          <div class="ipa-dashboard-hero-copy">
            <span class="ipa-hero-eyebrow">LIVE ANALYTICS WORKSPACE</span>
            <h2>Welcome back, {_safe_text(name)}.</h2>
            <p>Explore performance signals across {total:,} institutions and turn institutional data into clear, defensible decisions.</p>
            <div class="ipa-hero-pills">
              <span>✓ KPI Analytics</span>
              <span>✓ Rankings</span>
              <span>✓ Benchmarking</span>
              <span>✓ ML Intelligence</span>
            </div>
          </div>
          <div class="ipa-dashboard-hero-quote">
            <span>DECISION SUPPORT</span>
            <strong>"Data-driven insights for stronger, smarter institutions."</strong>
          </div>
        </div>
        """
    )


def _render_quick_actions() -> None:
    ui.html('<div class="ipa-quick-label">QUICK ACTIONS</div>')
    cols = st.columns(4)
    actions = [
        ("Upload Data", "Import and validate institutional datasets", "primary", "Data Management"),
        ("View Rankings", "Explore weighted institutional rankings", "success", "Rankings"),
        ("ML Predictions", "Review existing model predictions", "warning", "ML Predictions"),
        ("Generate Report", "Open the analytical report workspace", "accent", "Reports"),
    ]
    for col, (title, desc, tone, page) in zip(cols, actions):
        with col:
            ui.html(
                f"""
                <div class="ipa-action-card" data-tone="{tone}">
                  <div class="ipa-action-icon">{_safe_text(title[:1])}</div>
                  <div><strong>{_safe_text(title)}</strong><span>{_safe_text(desc)}</span></div>
                </div>
                """
            )
            if st.button(f"Open {title}", key=widget_key("dashboard", f"action_{page}"), use_container_width=True):
                st.session_state["dashboard_action"] = page
                st.info(f"Open **{page}** from the sidebar to continue.")


def _render_stat_cards(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> None:
    total = len(inst_df)
    avg_students = inst_df["student_enrollment"].mean() if not inst_df.empty else 0
    avg_placement = inst_df["placement_percentage"].mean() if not inst_df.empty else 0
    total_research = inst_df["research_publications"].sum() if not inst_df.empty else 0
    avg_overall = kpi_df["overall_performance_index"].mean() if not kpi_df.empty else 0
    top50 = int((kpi_df["institution_rank"] <= 50).sum()) if not kpi_df.empty else 0

    ui.stat_grid(
        [
            {"label": "Total Institutions", "value": _fmt_int(total), "hint": "Current analytics universe", "icon_name": "building", "tone": "primary"},
            {"label": "Avg Student Enrollment", "value": _fmt_int(avg_students), "hint": "Per institution", "icon_name": "users", "tone": "accent"},
            {"label": "Avg Placement", "value": f"{avg_placement:.1f}", "unit": "%", "hint": "Current institutional average", "icon_name": "briefcase", "tone": "success"},
            {"label": "Research Publications", "value": _fmt_int(total_research), "hint": "Across tracked institutions", "icon_name": "flask", "tone": "warning"},
            {"label": "Avg Overall KPI", "value": f"{avg_overall:.1f}", "hint": "0–100 performance index", "icon_name": "gauge", "tone": "primary"},
            {"label": "Top 50 Institutions", "value": _fmt_int(top50), "hint": "Based on current rank", "icon_name": "award", "tone": "accent"},
        ]
    )


def _render_kpi_landscape(kpi_df: pd.DataFrame) -> None:
    labels = [
        ("Academic", "academic_score"),
        ("Research", "research_score"),
        ("Placement", "placement_score"),
        ("Infrastructure", "infrastructure_score_kpi"),
        ("Faculty", "faculty_score"),
        ("Accreditation", "accreditation_score"),
    ]
    rows = []
    for label, col in labels:
        if col in kpi_df.columns:
            rows.append({"KPI": label, "Average Score": float(kpi_df[col].mean())})
    frame = pd.DataFrame(rows)
    if frame.empty:
        ui.empty_state("No KPI data", "Load KPI data to display the current performance landscape.", icon_name="chart-bar")
        return
    fig = px.bar(frame, x="KPI", y="Average Score", text="Average Score")
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", marker_color="#2F6FAD")
    fig.update_layout(
        template="plotly_white",
        height=330,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#fafbfd",
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(color="#0f1b2d"),
        showlegend=False,
    )
    fig.update_yaxes(range=[0, 100], gridcolor="#e8edf3", zeroline=False)
    fig.update_xaxes(showgrid=False)
    ui.chart(fig, key=widget_key("dashboard", "kpi_landscape"))


def _render_top_institutions(kpi_df: pd.DataFrame) -> None:
    if kpi_df.empty:
        ui.empty_state("No ranking data", "Ranking records will appear here after KPI processing.", icon_name="award")
        return
    columns = ["institution_name", "institution_rank", "composite_rank_score", "ranking_category"]
    frame = kpi_df[[c for c in columns if c in kpi_df.columns]].sort_values("institution_rank").head(6)
    rows = []
    for _, row in frame.iterrows():
        category = str(row.get("ranking_category", ""))
        rows.append(
            f"""<tr>
<td><span class="ipa-rank-badge">{int(row.get('institution_rank', 0))}</span></td>
<td><strong>{_safe_text(row.get('institution_name', ''))}</strong></td>
<td class="ipa-table-score">{float(row.get('composite_rank_score', 0)):.1f}</td>
<td>{ui.badge(category or 'Unclassified', _ranking_category_tone(category))}</td>
</tr>"""
        )
    markup = (
        '<div class="ipa-ranking-table-wrap">'
        '<table class="ipa-ranking-table">'
        '<thead><tr><th>#</th><th>Institution</th><th>Score</th><th>Category</th></tr></thead>'
        '<tbody>' + "".join(rows) + '</tbody>'
        '</table>'
        '</div>'
    )
    ui.html(markup)


def _render_insights(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> None:
    insights = InsightsService.generate_system_insights(inst_df, kpi_df)
    if not insights:
        ui.empty_state("No insights available", "System insights require both institution and KPI data.", icon_name="sparkles")
        return
    tone_cycle = ["success", "primary", "accent", "warning", "primary"]
    for idx, insight in enumerate(insights[:5]):
        ui.html(ui.insight_card(insight, label="System insight", tone=tone_cycle[idx % len(tone_cycle)]))


def render():
    user = get_current_user()
    data = load_data()
    inst_df = data["institutions"]
    kpi_df = data["kpis"]

    _render_dashboard_header(user)
    _render_hero(user, data)
    _render_quick_actions()
    show_data_banner(data)

    ui.html('<div class="ipa-dashboard-section-title"><span>PERFORMANCE SNAPSHOT</span><small>Live values from the current analytics dataset</small></div>')
    _render_stat_cards(inst_df, kpi_df)

    ui.html('<div class="ipa-dashboard-section-title"><span>ANALYTICS OVERVIEW</span><small>Evidence-first views of the current institutional dataset</small></div>')

    c1, c2 = st.columns([1.65, 1], gap="large")
    with c1:
        with ui.card(title="KPI Performance Landscape", subtitle="Average score across the six existing KPI dimensions.", icon_name="chart-bar"):
            _render_kpi_landscape(kpi_df)
    with c2:
        with ui.card(title="Top Performing Institutions", subtitle="Current weighted ranking results.", icon_name="award"):
            _render_top_institutions(kpi_df)

    c3, c4 = st.columns([1.15, 1], gap="large")
    with c3:
        with ui.card(title="Institution KPI Profile", subtitle="Compare one institution against the existing KPI dimensions.", icon_name="radar"):
            institutions = sorted(inst_df["institution_name"].dropna().tolist())
            if institutions:
                selected = st.selectbox(
                    "Institution",
                    institutions,
                    index=0,
                    key=widget_key("dashboard", "radar_institution"),
                    label_visibility="collapsed",
                )
                safe_plotly(kpi_comparison_chart, kpi_df, selected, page="dashboard", chart_name="radar")
            else:
                ui.empty_state("No institutions", "Institution records are required for comparison.", icon_name="building")
    with c4:
        with ui.card(title="Ranking Distribution", subtitle="Institutions grouped by current ranking category.", icon_name="pie-chart"):
            safe_plotly(ranking_distribution_chart, kpi_df, page="dashboard", chart_name="rank_dist")

    c5, c6 = st.columns(2, gap="large")
    with c5:
        with ui.card(title="Placement Analysis", subtitle="Placement rate versus the calculated placement KPI.", icon_name="briefcase"):
            safe_plotly(placement_analysis_chart, inst_df, kpi_df, page="dashboard", chart_name="placement")
    with c6:
        with ui.card(title="Research Analysis", subtitle="Research output versus the calculated research KPI.", icon_name="flask"):
            safe_plotly(research_analysis_chart, inst_df, kpi_df, page="dashboard", chart_name="research")

    ui.html('<div class="ipa-dashboard-section-title"><span>SYSTEM INSIGHTS</span><small>Generated from the existing analytics and benchmarking services</small></div>')
    with ui.card(title="Recent System Insights", subtitle="No fabricated trend claims — only insights derived from current records.", icon_name="sparkles"):
        _render_insights(inst_df, kpi_df)

    st.caption("Institutional Performance Analytics · Current dataset · SIH 2025")
