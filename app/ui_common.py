"""Shared UI helpers, sample data, and fallback content for all views."""
import pandas as pd
import plotly.express as px
import streamlit as st

from services.pipeline_service import PipelineService

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


def page_header(title: str, subtitle: str = "") -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


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
        st.warning(
            data.get(
                "sample_info",
                "Showing sample data. Go to **Data Management** → **Initialize / Reprocess All Data**.",
            )
        )
    elif data.get("partial_data"):
        st.warning(
            "Some analytics tables are empty. Open **Data Management** and run **Initialize / Reprocess All Data**."
        )


def render_kpi_cards(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Institutions", len(inst_df))
    c2.metric("Avg Placement %", f"{inst_df['placement_percentage'].mean():.1f}%")
    c3.metric("Avg Research Output", f"{inst_df['research_publications'].mean():.0f}")
    c4.metric("Avg Infrastructure", f"{inst_df['infrastructure_score'].mean():.1f}")

    if not kpi_df.empty and "overall_performance_index" in kpi_df.columns:
        c5, c6, c7 = st.columns(3)
        c5.metric("Avg Overall KPI", f"{kpi_df['overall_performance_index'].mean():.1f}")
        c6.metric("Top 50 Count", int((kpi_df["institution_rank"] <= 50).sum()))
        c7.metric("Avg Composite Score", f"{kpi_df['composite_rank_score'].mean():.1f}")


def render_sample_bar_chart(kpi_df: pd.DataFrame, title: str = "KPI Scores (Sample)") -> None:
    if kpi_df.empty:
        st.info("No KPI data for chart.")
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
        x=labels, y=values, title=title,
        labels={"x": "KPI", "y": "Score"},
        color=values, color_continuous_scale="Blues",
    )
    fig.update_layout(showlegend=False, yaxis_range=[0, 100], template="plotly_white")
    st.plotly_chart(fig, use_container_width=True, key=widget_key("chart", "sample_bar"))


def render_sample_pie_chart(kpi_df: pd.DataFrame, page: str = "dashboard") -> None:
    if kpi_df.empty or "ranking_category" not in kpi_df.columns:
        return
    counts = kpi_df["ranking_category"].value_counts().reset_index()
    counts.columns = ["category", "count"]
    fig = px.pie(counts, names="category", values="count", title="Ranking Category Distribution")
    st.plotly_chart(fig, use_container_width=True, key=widget_key(page, "sample_pie"))


def render_top_institutions_bar(kpi_df: pd.DataFrame, n: int = 5, page: str = "ranking") -> None:
    if kpi_df.empty:
        return
    n = max(1, min(n, len(kpi_df)))
    top = kpi_df.nsmallest(n, "institution_rank").sort_values("composite_rank_score", ascending=True)
    fig = px.bar(
        top, x="composite_rank_score", y="institution_name", orientation="h",
        title=f"Top {n} Institutions", template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True, key=widget_key(page, f"top_bar_{n}"))


def safe_plotly(chart_fn, *args, page: str = "chart", chart_name: str = "main", **kwargs):
    try:
        fig = chart_fn(*args, **kwargs)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, key=widget_key(page, chart_name))
    except Exception as exc:
        st.error(f"Chart could not be rendered: {exc}")
        for arg in args:
            if isinstance(arg, pd.DataFrame) and not arg.empty:
                render_sample_bar_chart(arg.head(1), title="Fallback KPI Chart")
                break
        else:
            render_sample_bar_chart(SAMPLE_KPIS.head(1), title="Fallback KPI Chart")


def filter_existing_columns(df: pd.DataFrame, columns: list) -> list:
    return [c for c in columns if c in df.columns]
