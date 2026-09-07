"""KPI Engine Overview."""
import pandas as pd
import streamlit as st

from app.ui_common import (
    filter_existing_columns,
    load_data,
    page_header,
    render_kpi_cards,
    render_sample_bar_chart,
    section_panel,
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

    section_panel("KPI Scoring System", "Published scoring definitions used by the analytics engine.")
    scoring_df = pd.DataFrame({
        "Metric": [
            "Academic Score",
            "Research Score",
            "Placement Score",
            "Infrastructure Score",
            "Faculty Score",
            "Accreditation Score",
            "Overall Performance Index",
        ],
        "Range": ["0-100"] * 7,
        "Formula": [
            "0.6 × Enrollment Score + 0.4 × NIRF Score",
            "Normalized Research Publications",
            "Placement Percentage",
            "Infrastructure Score",
            "Normalized Faculty Count",
            "Mapped from NAAC Grade",
            "Weighted Composite Score",
        ],
    })
    st.dataframe(scoring_df, use_container_width=True, hide_index=True)
    st.markdown(
        """
        **Overall Performance Index Weights**
        Academic 25% · Research 20% · Placement 25% · Infrastructure 5% · Faculty 15% · Accreditation 10%
        """
    )

    section_panel("Key Performance Indicator Analytics", "Analyze institutional performance across multiple dimensions.")
    total_inst = len(inst_df)
    avg_academic = round(kpi_df["academic_score"].mean(), 2)
    avg_research = round(kpi_df["research_score"].mean(), 2)
    avg_placement = round(kpi_df["placement_score"].mean(), 2)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Institutions", total_inst)
    with c2:
        st.metric("Academic", avg_academic)
    with c3:
        st.metric("Research", avg_research)
    with c4:
        st.metric("Placement", f"{avg_placement}%")

    section_panel("KPI Scorecards")
    render_kpi_cards(inst_df, kpi_df)

    display_df = kpi_df.merge(
        inst_df[
            [
                "institution_name",
                "state",
                "student_enrollment",
                "faculty_count",
                "accreditation_grade",
            ]
        ],
        on="institution_name",
        how="left",
    )
    display_cols = filter_existing_columns(
        display_df,
        [
            "institution_name",
            "state",
            "student_enrollment",
            "faculty_count",
            "academic_score",
            "research_score",
            "placement_score",
            "infrastructure_score_kpi",
            "faculty_score",
            "accreditation_score",
            "accreditation_grade",
            "overall_performance_index",
            "composite_rank_score",
            "institution_rank",
            "ranking_category",
        ],
    )

    section_panel("Institution KPI Explorer")
    search = st.text_input("Search Institution", "", key=widget_key("kpi", "filter"))
    filtered = display_df
    if search:
        filtered = display_df[
            display_df["institution_name"].str.contains(search, case=False, na=False)
        ]
    st.dataframe(
        filtered.sort_values("overall_performance_index", ascending=False)[display_cols],
        use_container_width=True,
        hide_index=True,
    )

    section_panel("KPI Visualization")
    render_sample_bar_chart(kpi_df.head(1), title="Top Institution KPI Breakdown")
    st.caption("Institutional Performance Analytics | KPI Intelligence Module")
