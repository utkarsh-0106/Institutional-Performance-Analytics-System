"""Plotly chart builders for analytics dashboard."""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


CHART_TEMPLATE = "plotly_white"
COLOR_PALETTE = px.colors.qualitative.Set2


def _has_statsmodels() -> bool:
    try:
        import statsmodels  # noqa: F401
        return True
    except ImportError:
        return False


def _scatter(df, x, y, title, hover_data=None, color_seq=None):
    kwargs = {
        "data_frame": df,
        "x": x,
        "y": y,
        "title": title,
        "template": CHART_TEMPLATE,
    }
    if hover_data:
        kwargs["hover_data"] = hover_data
    if color_seq:
        kwargs["color_discrete_sequence"] = color_seq
    if _has_statsmodels() and len(df) >= 3:
        kwargs["trendline"] = "ols"
    return px.scatter(**kwargs)


def kpi_comparison_chart(kpi_df: pd.DataFrame, institution_name: str = None) -> go.Figure:
    if kpi_df.empty:
        return go.Figure()
    kpi_cols = [
        "academic_score", "research_score", "placement_score",
        "infrastructure_score_kpi", "faculty_score", "accreditation_score",
    ]
    if institution_name:
        data = kpi_df[kpi_df["institution_name"] == institution_name]
        if data.empty:
            data = kpi_df.head(1)
    else:
        data = kpi_df.head(1)
    row = data.iloc[0]
    labels = [c.replace("_", " ").title().replace(" Score Kpi", "") for c in kpi_cols]
    values = [float(row[c]) for c in kpi_cols]
    fig = go.Figure(
        data=go.Scatterpolar(r=values, theta=labels, fill="toself", name=str(row["institution_name"]))
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="KPI Comparison (Radar)",
        polar=dict(radialaxis=dict(range=[0, 100])),
    )
    return fig


def top_institutions_chart(kpi_df: pd.DataFrame, n: int = 15) -> go.Figure:
    if kpi_df.empty:
        return go.Figure()
    n = max(1, min(int(n), len(kpi_df)))
    top = kpi_df.nsmallest(n, "institution_rank").sort_values("composite_rank_score", ascending=True)
    fig = px.bar(
        top,
        x="composite_rank_score",
        y="institution_name",
        orientation="h",
        title=f"Top {n} Institutions by Composite Score",
        color="composite_rank_score",
        color_continuous_scale="Blues",
        template=CHART_TEMPLATE,
    )
    fig.update_layout(height=max(400, n * 28), yaxis={"categoryorder": "total ascending"})
    return fig


def ranking_distribution_chart(kpi_df: pd.DataFrame) -> go.Figure:
    if kpi_df.empty:
        return go.Figure()
    counts = kpi_df["ranking_category"].value_counts().reset_index()
    counts.columns = ["ranking_category", "count"]
    fig = px.bar(
        counts,
        x="ranking_category",
        y="count",
        title="Ranking Category Distribution",
        color="ranking_category",
        template=CHART_TEMPLATE,
    )
    return fig


def placement_analysis_chart(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> go.Figure:
    if inst_df.empty or kpi_df.empty:
        return go.Figure()
    kpi_cols = ["institution_name", "placement_score"]
    kpi_subset = kpi_df[[c for c in kpi_cols if c in kpi_df.columns]]
    merged = inst_df.merge(kpi_subset, on="institution_name", how="inner")
    if merged.empty:
        return go.Figure()
    return _scatter(
        merged,
        "placement_percentage",
        "placement_score",
        "Placement Analysis",
        hover_data=["institution_name"],
    )


def research_analysis_chart(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> go.Figure:
    if inst_df.empty or kpi_df.empty:
        return go.Figure()
    kpi_subset = kpi_df[["institution_name", "research_score"]]
    merged = inst_df.merge(kpi_subset, on="institution_name", how="inner")
    if merged.empty:
        return go.Figure()
    return _scatter(
        merged,
        "research_publications",
        "research_score",
        "Research Output Analysis",
        hover_data=["institution_name"],
        color_seq=[COLOR_PALETTE[2]],
    )


def accreditation_analysis_chart(inst_df: pd.DataFrame, kpi_df: pd.DataFrame) -> go.Figure:
    if inst_df.empty or kpi_df.empty:
        return go.Figure()
    kpi_subset = kpi_df[["institution_name", "accreditation_score", "overall_performance_index"]]
    merged = inst_df.merge(kpi_subset, on="institution_name", how="inner")
    if merged.empty:
        return go.Figure()
    grade_avg = merged.groupby("accreditation_grade", as_index=False).agg(
        avg_accreditation_score=("accreditation_score", "mean"),
        avg_overall=("overall_performance_index", "mean"),
        count=("institution_name", "count"),
    )
    fig = px.bar(
        grade_avg,
        x="accreditation_grade",
        y="avg_overall",
        title="Accreditation Grade vs Overall Performance",
        color="avg_accreditation_score",
        template=CHART_TEMPLATE,
    )
    return fig


def benchmark_gap_chart(gaps: dict) -> go.Figure:
    if not gaps:
        return go.Figure()
    labels = [str(k).replace("_", " ").title() for k in gaps.keys()]
    values = [float(v) for v in gaps.values()]
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in values]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors))
    fig.update_layout(template=CHART_TEMPLATE, title="Performance Gaps vs Benchmarks")
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    return fig


def state_benchmark_chart(state_df: pd.DataFrame) -> go.Figure:
    if state_df.empty:
        return go.Figure()
    fig = px.bar(
        state_df.sort_values("avg_overall_kpi", ascending=False).head(15),
        x="state",
        y="avg_overall_kpi",
        title="State-wise Average Performance Index",
        template=CHART_TEMPLATE,
    )
    return fig
