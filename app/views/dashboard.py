"""Analytics Dashboard - Module 4."""
import streamlit as st

from app.components.charts import (
    accreditation_analysis_chart,
    kpi_comparison_chart,
    placement_analysis_chart,
    ranking_distribution_chart,
    research_analysis_chart,
    top_institutions_chart,
)
from app.ui_common import (
    load_data,
    page_header,
    render_kpi_cards,
    render_sample_bar_chart,
    render_sample_pie_chart,
    render_top_institutions_bar,
    safe_plotly,
    show_data_banner,
    widget_key,
)


def render():
    page_header(
        "Analytics Dashboard",
        "Institutional performance overview for UGC, AICTE, NAAC, and accreditation agencies",
    )

    data = load_data()
    show_data_banner(data)
    inst_df = data["institutions"]
    kpi_df = data["kpis"]

    st.subheader("Key Performance Indicators")
    render_kpi_cards(inst_df, kpi_df)

    st.divider()
    st.subheader("Charts & Analysis")

    institutions = sorted(inst_df["institution_name"].tolist())
    selected = st.selectbox(
        "Select institution for KPI radar",
        institutions,
        index=0,
        key=widget_key("dashboard", "radar_institution"),
    )

    c1, c2 = st.columns(2)
    with c1:
        safe_plotly(kpi_comparison_chart, kpi_df, selected, page="dashboard", chart_name="radar")
    with c2:
        safe_plotly(top_institutions_chart, kpi_df, min(15, len(kpi_df)), page="dashboard", chart_name="top15")

    c3, c4 = st.columns(2)
    with c3:
        if data.get("using_sample"):
            render_sample_pie_chart(kpi_df, page="dashboard")
        else:
            safe_plotly(ranking_distribution_chart, kpi_df, page="dashboard", chart_name="rank_dist")
    with c4:
        safe_plotly(placement_analysis_chart, inst_df, kpi_df, page="dashboard", chart_name="placement")

    c5, c6 = st.columns(2)
    with c5:
        safe_plotly(research_analysis_chart, inst_df, kpi_df, page="dashboard", chart_name="research")
    with c6:
        safe_plotly(accreditation_analysis_chart, inst_df, kpi_df, page="dashboard", chart_name="accreditation")

    if data.get("using_sample"):
        st.subheader("Additional Preview")
        render_top_institutions_bar(kpi_df, page="dashboard")
        render_sample_bar_chart(kpi_df)
