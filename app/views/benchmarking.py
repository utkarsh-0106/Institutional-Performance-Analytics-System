"""Benchmarking System - Module 8."""
import streamlit as st

from app.components.charts import benchmark_gap_chart, state_benchmark_chart
from app.ui_common import (
    load_data,
    page_header,
    render_sample_bar_chart,
    safe_plotly,
    section_panel,
    show_data_banner,
    widget_key,
)
from auth.session import get_current_user
from services.benchmarking_service import BenchmarkingService


def render():
    page_header("Benchmarking", "Compare against state, national, and top performer benchmarks")

    data = load_data()
    show_data_banner(data)
    inst_df = data["institutions"]
    kpi_df = data["kpis"]

    user = get_current_user()
    institutions = sorted(inst_df["institution_name"].tolist())
    default_inst = user.get("linked_institution") or institutions[0]
    default_idx = institutions.index(default_inst) if default_inst in institutions else 0
    selected = st.selectbox(
        "Select Institution",
        institutions,
        index=default_idx,
        key=widget_key("benchmarking", "institution"),
    )

    if data.get("using_sample"):
        section_panel("Sample Benchmark Preview")
        sample_gaps = {
            "placement_vs_national": 5.2,
            "research_vs_national": -8.1,
            "overall_vs_national": 3.4,
            "overall_vs_top": -12.5,
        }
        safe_plotly(benchmark_gap_chart, sample_gaps, page="benchmarking", chart_name="gaps")
        inst_kpi = kpi_df[kpi_df["institution_name"] == selected]
        render_sample_bar_chart(inst_kpi if not inst_kpi.empty else kpi_df.head(1))
        return

    comparison = BenchmarkingService.compare_institution(selected, inst_df, kpi_df)
    if not comparison:
        st.error("Could not generate comparison.")
        return

    section_panel(f"Analysis: {selected}")
    gaps = comparison.get("performance_gaps", {})
    if gaps:
        safe_plotly(benchmark_gap_chart, gaps, page="benchmarking", chart_name="gaps_live")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**National Benchmark**")
        for k, v in list(comparison.get("national_benchmark", {}).items())[:6]:
            st.write(f"{k.replace('_', ' ').title()}: **{v}**")
    with col2:
        st.markdown("**State Benchmark**")
        state = comparison.get("state_benchmark", {})
        if state:
            for k, v in list(state.items())[:6]:
                st.write(f"{k.replace('_', ' ').title()}: **{v}**")
        else:
            st.info("State data unavailable")
    with col3:
        st.markdown("**Top Performer Benchmark**")
        for k, v in list(comparison.get("top_performer_benchmark", {}).items())[:6]:
            st.write(f"{k.replace('_', ' ').title()}: **{v}**")

    state_df = BenchmarkingService.compute_state_averages(inst_df, kpi_df)
    if not state_df.empty:
        section_panel("State-wise Benchmarks")
        safe_plotly(state_benchmark_chart, state_df, page="benchmarking", chart_name="state")
        st.dataframe(state_df, use_container_width=True)
