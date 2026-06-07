"""Ranking System - Module 5."""
import streamlit as st

from app.ui_common import (
    filter_existing_columns,
    load_data,
    page_header,
    render_top_institutions_bar,
    show_data_banner,
    widget_key,
)
from services.ranking_engine import RankingEngine


def render():
    page_header(
        "Institution Rankings",
        "Weights: Academic 25% | Placement 25% | Research 20% | Infrastructure 15% | Faculty 10% | Accreditation 5%",
    )

    data = load_data()
    show_data_banner(data)
    kpi_df = data["kpis"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ranked", len(kpi_df))
    col2.metric("Top 50", int((kpi_df["institution_rank"] <= 50).sum()))
    col3.metric("Top 100", int((kpi_df["institution_rank"] <= 100).sum()))

    render_top_institutions_bar(kpi_df, n=min(10, len(kpi_df)), page="ranking")

    display_cols = filter_existing_columns(kpi_df, [
        "institution_rank", "institution_name", "composite_rank_score",
        "academic_score", "placement_score", "research_score",
        "infrastructure_score_kpi", "faculty_score", "accreditation_score",
        "ranking_category",
    ])

    tab1, tab2, tab3 = st.tabs(["Top 10", "Top 50", "Full Rankings"])
    with tab1:
        st.dataframe(RankingEngine.get_top_n(kpi_df, 10)[display_cols], use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(RankingEngine.get_top_n(kpi_df, 50)[display_cols], use_container_width=True, hide_index=True)
    with tab3:
        search = st.text_input("Search institution", "", key=widget_key("ranking", "search"))
        filtered = kpi_df
        if search:
            filtered = kpi_df[kpi_df["institution_name"].str.contains(search, case=False, na=False)]
        st.dataframe(
            filtered.sort_values("institution_rank")[display_cols],
            use_container_width=True,
            hide_index=True,
        )
