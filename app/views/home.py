"""Home page — landing content after login."""
import streamlit as st

from app.ui_common import (
    load_data,
    render_hero,
    render_kpi_cards,
    render_sample_bar_chart,
    section_panel,
    show_data_banner,
)
from auth.session import get_current_user


def render():
    user = get_current_user()

    data = load_data()
    inst_df = data["institutions"]
    kpi_df = data["kpis"]

    total_inst = len(inst_df)
    total_students = int(inst_df["student_enrollment"].sum())
    total_faculty = int(inst_df["faculty_count"].sum())
    avg_placement = round(inst_df["placement_percentage"].mean(), 2)

    render_hero(
        "Institutional Performance Analytics",
        "A unified workspace for KPI measurement, rankings, benchmarking, predictive analytics, and improvement recommendations across higher-education institutions.",
        "campus-quad.jpg",
    )

    st.caption(
        f"Signed in as {user.get('username', 'User')} · Role {str(user.get('role', '')).replace('_', ' ').title()}"
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Institutions", total_inst)
    with c2:
        st.metric("Students", f"{total_students:,}")
    with c3:
        st.metric("Faculty", f"{total_faculty:,}")
    with c4:
        st.metric("Avg Placement", f"{avg_placement}%")

    show_data_banner(data)

    section_panel("System Performance Overview", "Headline institutional metrics from the current dataset.")
    render_kpi_cards(inst_df, kpi_df)

    st.markdown(
        """
        <div class="ipa-chip-row">
            <span class="ipa-chip">Performance KPIs</span>
            <span class="ipa-chip">Rankings</span>
            <span class="ipa-chip">Benchmarking</span>
            <span class="ipa-chip">Predictive Analytics</span>
            <span class="ipa-chip">Recommendations</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_panel("Platform Modules", "Navigate from the sidebar to open each intelligence workspace.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Dashboard**\n\nInteractive analytics, KPI trends, and visual insights.")
        st.info("**Rankings**\n\nInstitution ranking based on weighted KPI scores.")
        st.info("**ML Predictions**\n\nForecast institutional performance from trained models.")
    with col2:
        st.info("**Data Management**\n\nUpload and process institutional datasets.")
        st.info("**KPI Overview**\n\nAcademic, research, and placement KPI explorer.")
        st.info("**Recommendations**\n\nGap-based improvement suggestions.")
    with col3:
        st.info("**Benchmarking**\n\nCompare nationally, by state, and against top performers.")
        st.info("**AI Insights**\n\nAutomated performance narratives.")
        st.info("**Reports**\n\nExport analytical PDF reports.")

    section_panel("Quick KPI Preview")
    render_sample_bar_chart(kpi_df, "Institution Performance Snapshot")
    st.caption("SIH 2025 · AICTE, UGC, NAAC & NIRF Institutional Analytics Platform")
