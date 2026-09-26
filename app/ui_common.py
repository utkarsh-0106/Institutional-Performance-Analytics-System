"""Shared UI helpers, sample data, and fallback content for all views.

Presentation concerns live in ``app.components.ui`` (the design system); this
module keeps the historical helper names and signatures that the 10 views
import, and delegates rendering to that system. Data access, sample fallbacks
and metric arithmetic are unchanged.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px

from app.components import ui
from services.pipeline_service import PipelineService

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
THEME_CSS_PATH = Path(__file__).resolve().parent / "theme.css"


def asset_path(filename: str) -> str:
    """Resolve a bundled asset (prefers an optimised WebP when one exists)."""
    return ui.asset_path(filename)


def image_data_uri(filename: str) -> str:
    """Base64 data URI for a bundled image, memoised across reruns."""
    return ui.image_data_uri(filename)


def inject_global_css() -> None:
    ui.inject_theme_css()

SAMPLE_INSTITUTIONS = pd.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "institution_name": [
        "Sample Institute of Technology",
        "National College of Engineering",
        "Premier Business School",
        "State Medical College",
        "Urban Polytechnic Institute",
    ],
    "student_enrollment": [5200, 8100, 3400, 2900, 1800],
    "faculty_count": [320, 480, 210, 380, 95],
    "placement_percentage": [78.5, 85.2, 72.0, 68.5, 61.0],
    "research_publications": [145, 320, 88, 410, 42],
    "infrastructure_score": [72.0, 88.5, 65.0, 79.0, 58.0],
    "accreditation_grade": ["A", "A+", "B++", "A", "B+"],
    "nirf_rank": [120, 45, 210, 95, 350],
    "state": ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat"],
})

SAMPLE_KPIS = pd.DataFrame({
    "institution_id": [1, 2, 3, 4, 5],
    "institution_name": SAMPLE_INSTITUTIONS["institution_name"],
    "academic_score": [72.5, 88.0, 65.0, 80.0, 55.0],
    "research_score": [58.0, 82.0, 45.0, 90.0, 30.0],
    "placement_score": [78.5, 85.2, 72.0, 68.5, 61.0],
    "infrastructure_score_kpi": [72.0, 88.5, 65.0, 79.0, 58.0],
    "faculty_score": [68.0, 85.0, 62.0, 75.0, 50.0],
    "accreditation_score": [80.0, 90.0, 70.0, 80.0, 60.0],
    "overall_performance_index": [71.2, 86.5, 63.8, 78.5, 52.0],
    "composite_rank_score": [70.8, 86.1, 63.2, 78.0, 51.5],
    "institution_rank": [3, 1, 4, 2, 5],
    "ranking_category": ["Top 50", "Top 50", "Top 200", "Top 50", "Beyond 200"],
})

SAMPLE_PREDICTIONS = pd.DataFrame({
    "institution_id": [1, 2, 3, 4, 5],
    "institution_name": SAMPLE_INSTITUTIONS["institution_name"],
    "predicted_performance_score": [71.0, 87.5, 64.0, 79.0, 53.0],
    "accreditation_readiness": ["Ready", "Ready", "Partially Ready", "Ready", "Not Ready"],
    "ranking_category_pred": ["Top 50", "Top 50", "Top 200", "Top 50", "Beyond 200"],
})

SAMPLE_RECOMMENDATIONS = pd.DataFrame({
    "institution_id": [1, 1, 3, 5],
    "institution_name": [
        "Sample Institute of Technology",
        "Sample Institute of Technology",
        "Premier Business School",
        "Urban Polytechnic Institute",
    ],
    "category": ["Research", "Placement", "Research", "Faculty"],
    "message": [
        "Recommend increasing publications and research grants.",
        "Recommend stronger industry partnerships for placements.",
        "Recommend increasing publications and research grants.",
        "Recommend faculty development programs and PhD hiring.",
    ],
    "priority": ["high", "medium", "high", "high"],
})


def widget_key(page: str, name: str) -> str:
    """Unique Streamlit widget keys per page (prevents DuplicateWidgetID errors)."""
    return f"{page}__{name}"


def page_header(title: str, subtitle: str = "", kicker_text: str = "", right: str = "") -> None:
    ui.page_header(title, subtitle, kicker_text=kicker_text or None, right=right or None)


def section_panel(title: str, body: str = "") -> None:
    """Section heading for the not-yet-migrated views (no wrapper div)."""
    ui.html(ui.section_head(title, subtitle=body or None))


def render_hero(title: str, description: str, image_file: str, kicker: str = "Institutional Intelligence") -> None:
    ui.hero(title, description, image_file=image_file, kicker_text=kicker)


def load_data() -> dict:
    """Load DB data with safe fallback to sample datasets."""
    try:
        data = PipelineService().get_all_data()
        inst = data.get("institutions", pd.DataFrame())
        kpi = data.get("kpis", pd.DataFrame())
        if inst.empty or kpi.empty:
            return _sample_data_bundle("Database empty — showing sample preview data.")
        data["institutions"] = inst
        data["kpis"] = kpi
        data["predictions"] = data.get("predictions", pd.DataFrame())
        data["recommendations"] = data.get("recommendations", pd.DataFrame())
        data["using_sample"] = False
        if data["predictions"].empty or data["recommendations"].empty:
            data["partial_data"] = True
        else:
            data["partial_data"] = False
        return data
    except Exception as exc:
        return _sample_data_bundle(f"Could not load database: {exc}")


def _sample_data_bundle(info_msg: str) -> dict:
    return {
        "institutions": SAMPLE_INSTITUTIONS.copy(),
        "kpis": SAMPLE_KPIS.copy(),
        "predictions": SAMPLE_PREDICTIONS.copy(),
        "recommendations": SAMPLE_RECOMMENDATIONS.copy(),
        "using_sample": True,
        "partial_data": False,
        "sample_info": info_msg,
    }


def show_data_banner(data: dict) -> None:
    if data.get("using_sample"):
        # sample_info is generated by load_data() — plain text, so it is escaped.
        detail = data.get("sample_info") or (
            "Showing sample data. Go to <strong>Data Management</strong> and run "
            "<strong>Initialize / Reprocess All Data</strong>."
        )
        ui.html(ui.note(
            title="Sample data in use",
            body=ui.esc(detail),
            tone="warning",
            icon_name="alert-triangle",
        ))
    elif data.get("partial_data"):
        ui.html(ui.note(
            title="Incomplete analytics tables",
            body="Some analytics tables are empty. Open <strong>Data Management</strong> and run "
                 "<strong>Initialize / Reprocess All Data</strong>.",
            tone="warning",
            icon_name="alert-triangle",
        ))


def render_kpi_cards(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> None:
    """Headline metrics. Arithmetic is identical to the previous metrics row."""
    items = [
        {"label": "Total Institutions", "value": len(inst_df), "icon_name": "building", "tone": "primary"},
        {"label": "Avg Placement %", "value": f"{inst_df['placement_percentage'].mean():.1f}",
         "unit": "%", "icon_name": "briefcase", "tone": "accent"},
        {"label": "Avg Research Output", "value": f"{inst_df['research_publications'].mean():.0f}",
         "icon_name": "flask", "tone": "primary"},
        {"label": "Avg Infrastructure", "value": f"{inst_df['infrastructure_score'].mean():.1f}",
         "icon_name": "layers", "tone": "primary"},
    ]

    if not kpi_df.empty and "overall_performance_index" in kpi_df.columns:
        items += [
            {"label": "Avg Overall KPI", "value": f"{kpi_df['overall_performance_index'].mean():.1f}",
             "icon_name": "gauge", "tone": "primary"},
            {"label": "Top 50 Count", "value": int((kpi_df["institution_rank"] <= 50).sum()),
             "icon_name": "award", "tone": "accent"},
            {"label": "Avg Composite Score", "value": f"{kpi_df['composite_rank_score'].mean():.1f}",
             "icon_name": "target", "tone": "primary"},
        ]

    ui.stat_grid(items)


def _chart_layout(fig, showlegend: bool = False) -> None:
    """Shared light Plotly surface. Font family is left to the design system CSS."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=ui.COLORS["surface"],
        plot_bgcolor="#fafbfd",
        font=dict(color=ui.COLORS["text"]),
        margin=dict(l=24, r=24, t=26, b=28),
        showlegend=showlegend,
        hoverlabel=dict(font=dict(size=13)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=12, color=ui.COLORS["muted"])),
    )


def render_sample_bar_chart(kpi_df: pd.DataFrame, title: str = "KPI Scores (Sample)") -> None:
    if kpi_df.empty:
        ui.empty_state(
            "No KPI data for this chart",
            "Load institutional KPI data to visualise component scores.",
            icon_name="chart-bar",
        )
        return
    row = kpi_df.iloc[0]
    labels = ["Academic", "Research", "Placement", "Infrastructure", "Faculty", "Accreditation"]
    values = [
        float(row.get("academic_score", 0)),
        float(row.get("research_score", 0)),
        float(row.get("placement_score", 0)),
        float(row.get("infrastructure_score_kpi", 0)),
        float(row.get("faculty_score", 0)),
        float(row.get("accreditation_score", 0)),
    ]
    fig = px.bar(
        x=labels, y=values,
        labels={"x": "", "y": "Score"},
        color_discrete_sequence=[ui.COLORS["primary"]],
    )
    _chart_layout(fig)
    fig.update_yaxes(range=[0, 100], gridcolor=ui.COLORS["grid"], zeroline=False, ticksuffix="")
    fig.update_xaxes(showgrid=False)
    ui.chart(fig, key=widget_key("chart", "sample_bar"),
             note_text="Component scores out of 100 for a single institution.")


def render_sample_pie_chart(kpi_df: pd.DataFrame, page: str = "dashboard") -> None:
    if kpi_df.empty or "ranking_category" not in kpi_df.columns:
        return
    counts = kpi_df["ranking_category"].value_counts().reset_index()
    counts.columns = ["category", "count"]
    fig = px.pie(counts, names="category", values="count", hole=0.55,
                 color_discrete_sequence=[ui.COLORS["primary"], ui.COLORS["primary_600"],
                                          ui.COLORS["accent"], ui.COLORS["primary_400"]])
    _chart_layout(fig, showlegend=True)
    fig.update_traces(textposition="inside", textinfo="percent+label", sort=False,
                      textfont=dict(size=12, color="#ffffff"))
    ui.chart(fig, key=widget_key(page, "sample_pie"),
             note_text="Institutions grouped by ranking category.")


def render_top_institutions_bar(kpi_df: pd.DataFrame, n: int = 5, page: str = "ranking") -> None:
    if kpi_df.empty:
        return
    n = max(1, min(n, len(kpi_df)))
    top = kpi_df.nsmallest(n, "institution_rank").sort_values("composite_rank_score", ascending=True)
    fig = px.bar(
        top, x="composite_rank_score", y="institution_name", orientation="h",
        color_discrete_sequence=[ui.COLORS["primary"]],
    )
    _chart_layout(fig)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(gridcolor=ui.COLORS["grid"], zeroline=False)
    fig.update_yaxes(showgrid=False, tickfont=dict(size=12))
    ui.chart(fig, key=widget_key(page, f"top_bar_{n}"),
             note_text=f"Composite rank score (0–100) for the top {n} ranked institutions.")


def safe_plotly(chart_fn, *args, page: str = "chart", chart_name: str = "main", **kwargs):
    """Render a Plotly figure, or surface the real error.

    There is deliberately no synthetic fallback chart: a fabricated KPI chart
    is worse than an honest error state. The technical detail stays available.
    """
    try:
        fig = chart_fn(*args, **kwargs)
    except Exception as exc:
        ui.error_state(
            title="This chart could not be rendered",
            body="The underlying analytics could not be plotted. Review the data source or filters, then retry.",
            exc=exc,
        )
        return
    if fig is None:
        return
    ui.chart(fig, key=widget_key(page, chart_name))


def filter_existing_columns(df: pd.DataFrame, columns: list) -> list:
    return [c for c in columns if c in df.columns]
