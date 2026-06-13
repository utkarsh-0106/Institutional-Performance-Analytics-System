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
        "Weighted Ranking Framework for Higher Education Institutions",
    )

    st.markdown("""
    ## 🏆 Institutional Ranking Intelligence

    Compare institutions using a composite performance score generated from
    Academic, Research, Placement, Infrastructure, Faculty and Accreditation KPIs.
    """)

    data = load_data()
    show_data_banner(data)

    kpi_df = data["kpis"]

    total_ranked = len(kpi_df)
    top50 = int((kpi_df["institution_rank"] <= 50).sum())
    top100 = int((kpi_df["institution_rank"] <= 100).sum())

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("🏫 Total Ranked", total_ranked)

    with c2:
        st.metric("🥇 Top 50", top50)

    with c3:
        st.metric("🏆 Top 100", top100)

    st.markdown("---")

    st.info("""
    **Ranking Formula**

    Academic (20%) • Research (20%) • Placement (20%) •
    Infrastructure (15%) • Faculty (15%) • Accreditation (10%)
    """)

    st.markdown("## 📈 Top Performing Institutions")

    render_top_institutions_bar(
        kpi_df,
        n=min(10, len(kpi_df)),
        page="ranking",
    )

    display_cols = filter_existing_columns(
        kpi_df,
        [
            "institution_rank",
            "institution_name",
            "composite_rank_score",
            "academic_score",
            "placement_score",
            "research_score",
            "infrastructure_score_kpi",
            "faculty_score",
            "accreditation_score",
            "ranking_category",
        ],
    )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(
        [
            "🥇 Top 10",
            "🏆 Top 50",
            "🔍 Ranking Explorer",
        ]
    )

    with tab1:

        st.markdown("### Top 10 Institutions")

        st.dataframe(
            RankingEngine.get_top_n(
                kpi_df,
                10,
            )[display_cols],
            use_container_width=True,
            hide_index=True,
        )

    with tab2:

        st.markdown("### Top 50 Institutions")

        st.dataframe(
            RankingEngine.get_top_n(
                kpi_df,
                50,
            )[display_cols],
            use_container_width=True,
            hide_index=True,
        )

    with tab3:

        st.markdown("### Search & Explore Rankings")

        search = st.text_input(
            "🔍 Search Institution",
            "",
            key=widget_key(
                "ranking",
                "search",
            ),
        )

        filtered = kpi_df

        if search:
            filtered = kpi_df[
                kpi_df["institution_name"].str.contains(
                    search,
                    case=False,
                    na=False,
                )
            ]

        st.dataframe(
            filtered.sort_values(
                "institution_rank"
            )[display_cols],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.caption(
        "Institutional Performance Analytics | Ranking Intelligence Engine"
    )