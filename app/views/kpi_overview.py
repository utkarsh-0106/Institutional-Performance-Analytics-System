"""KPI Engine Overview."""
import streamlit as st

from app.ui_common import (
    filter_existing_columns,
    load_data,
    page_header,
    render_kpi_cards,
    render_sample_bar_chart,
    show_data_banner,
    widget_key,
)


def render():
    page_header(
        "KPI Overview",
        "Academic, Research, Placement, Infrastructure, Faculty, Accreditation & Overall Performance Index",
    )

    data = load_data()
    show_data_banner(data)
    kpi_df = data["kpis"]
    inst_df = data["institutions"]

    st.subheader("Aggregate KPI Metrics")
    render_kpi_cards(inst_df, kpi_df)

    display_cols = filter_existing_columns(kpi_df, [
        "institution_name", "academic_score", "research_score", "placement_score",
        "infrastructure_score_kpi", "faculty_score", "accreditation_score",
        "overall_performance_index", "composite_rank_score", "institution_rank",
    ])

    st.divider()
    st.subheader("Institution KPI Table")
    search = st.text_input("Filter by institution name", "", key=widget_key("kpi", "filter"))
    filtered = kpi_df
    if search:
        filtered = kpi_df[kpi_df["institution_name"].str.contains(search, case=False, na=False)]

    st.dataframe(
        filtered.sort_values("overall_performance_index", ascending=False)[display_cols],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("KPI Distribution Chart")
    render_sample_bar_chart(kpi_df.head(1), title="Top Institution KPI Breakdown")
